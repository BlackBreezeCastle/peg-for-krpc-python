import krpc
import time
import mission
from peg import *

def SetAllEngineGimbalLocked(vessel,IsLocked):
    if vessel==None:
        return None
    parts=vessel.parts.engines
    if parts==None:
        return None
    for i in parts:
        if i.gimballed==True:
            i.gimbal_locked= IsLocked  

conn = krpc.connect(name='test')
vessel = conn.space_center.active_vessel
SetAllEngineGimbalLocked(vessel,False)
body=vessel.orbit.body
reference_frame=body.non_rotating_reference_frame

lead_time=7651776.534758-3600
target_pe=150000.00000001490000000+6371000
target_ap= 416392613.35923040000000000+6371000
target_lan=math.radians(0.59637608190271463)
target_inc=math.radians(28.5)
target_aop=math.radians(164.59591855330967000)
turn_angle=4.0
target_normal_vector=target_normal_vector(conn,body,target_inc,target_lan,reference_frame)

#conn.space_center.warp_to(lead_time)
'''
position=conn.add_stream(vessel.position,reference_frame)
velocity=conn.add_stream(vessel.velocity,reference_frame)
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
speed=conn.add_stream(getattr, vessel.flight(reference_frame), 'speed')
horizontal_speed=conn.add_stream(getattr, vessel.flight(body.reference_frame), 'horizontal_speed')
vertical_speed=conn.add_stream(getattr, vessel.flight(body.reference_frame), 'vertical_speed')
'''
peg=pegas(conn)
peg.set_ref_target(target_pe,target_ap,target_inc,target_lan,target_aop)
peg.update_stages()
peg.vehicle_info()
input()
warp_to_launch(conn,target_inc,target_lan,False)

pitch=90
yaw=math.degrees(target_heading(vessel,target_normal_vector,reference_frame))
vessel.auto_pilot.engage()
vessel.auto_pilot.time_to_peak=(6,6,6)
vessel.auto_pilot.stopping_time=(0.2,0.2,0.2)
vessel.auto_pilot.attenuation_angle=(0.2,0.5,0.2)
vessel.auto_pilot.reference_frame=reference_frame
vessel.auto_pilot.shutdown_speed=3e8
vessel.auto_pilot.max_acceleration(4.5*9.8067)
vessel.auto_pilot.target_pitch=pitch
vessel.auto_pilot.target_roll=math.nan
vessel.control.rcs=False
''
#vessel.auto_pilot.target_pitch=90
#vessel.auto_pilot.attenuation_angle=(0.2,0.2,0.2)

fair_droped=False
stage_one_droped=False
sediment=False
#fair_droped=True
#stage_one_droped=True
countdown=10
while countdown>0:
    if countdown==6:
        print('ingition!')
        vessel.control.throttle = 1.0
        vessel.control.activate_next_stage()
    else:
        print(countdown)
    countdown=countdown-1
    time.sleep(1)

print('lift off')
vessel.control.activate_next_stage()

turn_start_altitude = vessel.flight().mean_altitude+50
while vessel.flight().mean_altitude<turn_start_altitude:
    time.sleep(0.1)

print('start gravity turn')
vessel.auto_pilot.target_roll=0.0


while vessel.flight().mean_altitude<turn_start_altitude+500:
    ''
    pitch = 90-turn_angle*min((vessel.flight().mean_altitude - turn_start_altitude) /300,1)
    yaw=math.degrees(target_heading(vessel,target_normal_vector,reference_frame))
    vessel.auto_pilot.target_pitch_and_heading(pitch,yaw)
    #time.sleep(0.1)

print('gravity turning')
while vessel.flight().mean_altitude<30000:
    ''
    vertical_speed=vessel.flight(body.reference_frame).vertical_speed
    horizontal_speed=vessel.flight(body.reference_frame).horizontal_speed
    pitch=math.degrees(math.atan(vertical_speed/horizontal_speed))
    yaw=math.degrees(target_heading(vessel,target_normal_vector,reference_frame))
    vessel.auto_pilot.target_pitch_and_heading(pitch,yaw)


''
print('pega running')
vessel.auto_pilot.attenuation_angle=(0.2,0.5,0.2)
vessel.auto_pilot.stopping_time=(0.1,0.1,0.1)
vessel.auto_pilot.time_to_peak=(5,5,5)
peg.update_stages()
peg.vehicle_info()
for i in range(100):
    peg.update()
tgo=1e10  

while True:
    acc=vessel.thrust/max(vessel.mass,0.1)
    if tgo>10:
        py=peg.update()
    else:
        py=peg.slerp()
    if py!=None:
        pitch=py[0]
        yaw=py[1]
    tgo=peg.time_to_go()
    time_to_stage=peg.time_to_stage()
    rd=peg.rd_position()
    print('tgo:%f pitch:%f yaw:%f acc:%f time_to_stage:%f pos: %f %f'%(tgo,math.degrees(pitch),math.degrees(yaw),acc,time_to_stage,rd[0],rd[1]),end='\r')

    #print('tgo',tgo)
    #print('py',py)
    vessel.auto_pilot.target_pitch_and_heading(math.degrees(pitch),math.degrees(yaw))    
    if fair_droped==False and vessel.flight().mean_altitude>100000:
        fair_droped=True
        vessel.control.activate_next_stage()
        time.sleep(0.5)
        peg.update_stages()

    if  time_to_stage<1.0:
        if stage_one_droped==False:
            stage_one_droped=True
            vessel.control.rcs=True
            vessel.control.activate_next_stage()
            time.sleep(2.0)
            vessel.control.activate_next_stage()
            for i in range(20):
                peg.update()
    else:
        stage_one_droped=False
    
    if acc<1:
        if sediment==False:
            vessel.control.forward=1.0
            vessel.auto_pilot.stopping_time=(300,0.1,300)
        sediment=True
    else:
        if sediment==True:
            vessel.auto_pilot.stopping_time=(0.1,0.1,0.1)
            vessel.control.forward=0.0
        sediment=False
    if tgo<0.2:
        vessel.auto_pilot.shutdown_speed=0
        vessel.control.throttle = 0.0
        break
    if  vessel.orbit.apoapsis>target_ap:
        vessel.auto_pilot.shutdown_speed=0
        vessel.control.throttle = 0.0
        break
vessel.control.rcs=False
SetAllEngineGimbalLocked(vessel,True)
time.sleep(1)
time.sleep(1)
input()
vessel.auto_pilot.disengage()

