import krpc
import time

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
    r=body.equatorial_radius
    gm=body.gravitational_parameter
    new_pe=r+new_pe
    ap=r+ap
    sem=0.5*(new_pe+ap)
    return math.sqrt(2.0*(gm/ap-0.5*gm/sem))

conn = krpc.connect()
vessel = conn.space_center.active_vessel
SetAllEngineGimbalLocked(vessel,True)
body=vessel.orbit.body


orbit=vessel.orbit
gm=orbit.body.gravitational_parameter
geo_period=body.rotational_period
vessel.control.rcs=True

while True:
    print('orbit error',orbit.period-geo_period)


