import krpc
import time
from peg import *
conn = krpc.connect()
vessel = conn.space_center.active_vessel
body=vessel.orbit.body
reference_frame=vessel.orbit.body.non_rotating_reference_frame

#radiu of the orbit injection point ,180000 is the altitude
target_radius = 180000+6371000
#speed in the orbit injection point
target_speed=7800
#longitude of ascending node in the target orbit
target_lan=math.radians(102)
#inclination of the target orbit
target_inc=math.radians(42)
#the angle between the velocity and the horizontal plane in the orbit injection point
target_angle=math.radians(0.0)




#the follow yaw can work for gravity turn
target_normal_vector=target_normal_vector(conn,body,target_inc,target_lan,reference_frame)
yaw=math.degrees(target_heading(vessel,target_normal_vector,reference_frame))





#initialize the peg
peg=pegas(conn)
peg.set_target(target_inc,target_lan,target_radius,target_speed)
#the function 'update_stages()' only work for those rocket with out any auxiliary booster
#it obtains the dry mass,total mass,specific ,impulse and thrust of each stages
#run it when initialize the peg or when the dry mass of the rock changes such as just droped fairings
#need run it when the acceleration exceeds 4.5g 
peg.update_stages()



#the peg works like this
#In general the algorithm will diverge when tgo <3
pitch=0.0
yaw=0.0
py=peg.update()
tgo=peg.time_to_go()
if py!=None and tgo>3:
    pitch=py[0]
    yaw=py[1]
print('tgo:%f pitch %f yaw %f'%(tgo,math.degrees(pitch),math.degrees(yaw)),end='\r')




#the following code works to limit the max acceleration
const_acc==False
acc=vessel.thrust/max(vessel.mass,0.1)
if acc>9.8067*4.5 and const_acc==False:
    const_acc=True
    peg.update_stages()

throttle_bias=Ktimer.integrator()   
dacc=acc-9.8067*4.5
#when the throttle fluctuating ,set the k a lower number
k=0.5
if const_acc==True:
    vessel.control.throttle = 1.0-k*throttle_bias.integral(dacc)