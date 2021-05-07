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

conn = krpc.connect()
vessel = conn.space_center.active_vessel
SetAllEngineGimbalLocked(vessel,True)
body=vessel.orbit.body


orbit=vessel.orbit
gm=orbit.body.gravitational_parameter
geo_period=body.rotational_period
sem=pow((0.5*geo_period/math.pi)**2*gm,1.0/3.0)
#sem=68000000
print('sem',sem-6371000)
reference_frame=vessel.orbit.body.non_rotating_reference_frame

#radiu of the orbit injection point ,180000 is the altitude
target_radius = 180000+6371000

target_lan=math.radians(mission.target_lan)
target_inc=math.radians(mission.target_inc)


#initialize the peg
peg=pegas(conn)
peg.set_ref_target(target_radius,sem,target_inc,target_lan,math.pi)
#the function 'update_stages()' only work for those rocket with out any auxiliary booster
#it obtains the dry mass,total mass,specific ,impulse and thrust of each stages
#run it when initialize the peg or when the dry mass of the rock changes such as just droped fairings
#need run it when the acceleration exceeds 4.5g 
peg.add_stage(vessel.mass,vessel.dry_mass,vessel.max_thrust,vessel.vacuum_specific_impulse,3)
peg.vehicle_info()


#the peg works like this
#In general the algorithm will diverge when tgo <3
pitch=0.0
yaw=0.0
angle_to_rd=0.0
vessel.auto_pilot.attenuation_angle=(0.2,0.2,0.2)
vessel.auto_pilot.stopping_time=(10,0.2,10)
vessel.auto_pilot.time_to_peak=(18,6,18)
vessel.auto_pilot.target_roll=0
vessel.auto_pilot.engage()
vessel.auto_pilot.shutdown_speed=3e8
#vessel.control.throttle = 1.0
lighter=OverMin()
vessel.control.rcs=True

for i in range(0,200):
    peg.update()
while True:
    py=peg.update()
    tgo=peg.time_to_go()
    if lighter.update(tgo)>20 and vessel.control.throttle <1.0:
        print('\n2st stage second ignition\n')
        SetAllEngineGimbalLocked(vessel,False)
        vessel.control.throttle = 1.0
        vessel.auto_pilot.stopping_time=(0.1,0.5,0.1)
    if py!=None and tgo>10:
        pitch=math.degrees(py[0])
        yaw=math.degrees(py[1])
        angle_to_rd=peg.angle_to_rd()
    rd=peg.rd_position()
    #print('\n\n\n\n')
    print('tgo:%f pitch:%f yaw:%f pos: %f %f'%(tgo,pitch,yaw,rd[0],rd[1]),end='\r')
    vessel.auto_pilot.target_pitch_and_heading(pitch,yaw)
    #print('tgo:%f pitch:%f yaw:%f angle_to_rd:%f'%(tgo,math.degrees(pitch),math.degrees(yaw),math.degrees(angle_to_rd)),end='\r')
    if  orbit.apoapsis>sem-50000:
        vessel.control.throttle = 0.0
        break


