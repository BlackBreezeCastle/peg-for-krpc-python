import krpc
import math
conn = krpc.connect(name='mission')
#target_lan=math.degrees(conn.space_center.bodies['Moon'].orbit.longitude_of_ascending_node)
#target_inc=math.degrees(conn.space_center.bodies['Moon'].orbit.inclination)
#print('target_inc',target_inc)
conn.close()
''
target_lan=150
target_inc=19.5
''
is_launch_to_north=False
target_speed=7800.367973
#target_speed=7899.693014
target_altitude =180000
#target_altitude =140000

#turn_angle=3.8 #for falcon 9
#turn_angle=3.0 #for falcon 10 leo
#turn_angle=2.8 #for falcon 10 lto
#turn_angle=3.8 #for kuai zhou leo
turn_angle=3.8 #for kuai zhou gto