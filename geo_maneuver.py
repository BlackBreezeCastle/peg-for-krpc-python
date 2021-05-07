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

def ApSpeed(new_pe,ap,body):
    gm=body.gravitational_parameter
    sem=0.5*(new_pe+ap)
    return math.sqrt(2.0*(gm/ap-0.5*gm/sem))

conn = krpc.connect()
vessel = conn.space_center.active_vessel
SetAllEngineGimbalLocked(vessel,True)
body=vessel.orbit.body


orbit=vessel.orbit
gm=orbit.body.gravitational_parameter
geo_period=body.rotational_period
pe=pow((0.5*geo_period/math.pi)**2*gm,1.0/3.0)
#sem=68000000
print('pe',pe-body.equatorial_radius)
reference_frame=vessel.orbit.body.non_rotating_reference_frame

#radiu of the orbit injection point ,180000 is the altitude

target_radius = orbit.apoapsis
target_speed=ApSpeed(pe,target_radius,body)
target_lan=math.radians(0)
target_inc=math.radians(0)

print('target_speed',target_speed)
#initialize the peg
peg=pegas(conn)
#the function 'update_stages()' only work for those rocket with out any auxiliary booster
#it obtains the dry mass,total mass,specific ,impulse and thrust of each stages
#run it when initialize the peg or when the dry mass of the rock changes such as just droped fairings
#need run it when the acceleration exceeds 4.5g 
peg.add_stage(vessel.mass,vessel.dry_mass,1113.8*4,321.8,3)
peg.vehicle_info()
peg.set_std_target(target_inc,target_lan,target_radius,target_speed,0.0)

#the peg works like this
#In general the algorithm will diverge when tgo <3
pitch=0.0
yaw=0.0
angle_to_rd=0.0
vessel.auto_pilot.attenuation_angle=(0.2,0.2,0.2)
vessel.auto_pilot.stopping_time=(0.5,0.5,0.5)
vessel.auto_pilot.time_to_peak=(3,3,3)
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
        #target_radius = pe #vessel.flight().mean_altitude+body.equatorial_radius
        #target_speed=ApSpeed(pe,target_radius,body)
        peg.set_std_target(target_inc,target_lan,target_radius,target_speed,0.0)
        for i in range(0,50):
            peg.update()
        print('\n2st stage second ignition\n')
        conn.space_center.rails_warp_factor=0
        SetAllEngineGimbalLocked(vessel,False)
        vessel.control.forward=1.0
        time.sleep(5)
        vessel.control.throttle = 1.0
        vessel.control.forward=0.0
        #vessel.auto_pilot.stopping_time=(0.1,0.5,0.1)
    if py!=None and tgo>3:
        pitch=math.degrees(py[0])
        yaw=math.degrees(py[1])
        angle_to_rd=peg.angle_to_rd()
    rd=peg.rd_position()
    #print('\n\n\n\n')
    print('tgo:%f pitch:%f yaw:%f pos: %f %f'%(tgo,pitch,yaw,rd[0],rd[1]),end='\r')
    vessel.auto_pilot.target_pitch_and_heading(pitch,yaw)
    #print('tgo:%f pitch:%f yaw:%f angle_to_rd:%f'%(tgo,math.degrees(pitch),math.degrees(yaw),math.degrees(angle_to_rd)),end='\r')
    if  tgo<0.2:
        vessel.control.throttle = 0.0
        break

vessel.control.rcs=False
