from Kmath import *

class orbit:
    def __init__(self,u):
        self.__e=0.0
        self.__u=u
        self.__f=0.0
        self.__t=0.0
        self.__h=Vector3(0.0,0.0,0.0)
        self.__f0=Vector3(0.0,0.0,0.0)    
    def set_r_v_t(self,r,v,t,u):
        self.__t=t
        self.__h=Vector3.Cross(v,r)
        hh=Vector3.Dot(self.__h,self.__h)
        energy=0.5*v.mag()**2-u/r.mag()
        if energy==0.0:
            self.__e=1.0
        else:
            a=-0.5*u/energy
            self.__e=(1-hh/(a*u))**0.5
        
        if self.__e!=0.0:
            cosf=(hh/(self.__u*r.mag())-1)/self.__e
            cosf=max(-1.0,min(1.0,cosf))
            self.__f=abs(math.acos(cosf))
            if Vector3.Dot(r,v)<0:
                self.__f=-1*self.__f
            print(self.__f)

    def get_flight_angle(self,f):
        return math.atan(self.__e*math.sin(f)/(1+self.__e*math.cos(f)))
    
    def get_a(self):
        return Vector3.Dot(self.__h,self.__h)/(self.__u*(1-self.__e**2))

    def get_pe(self):
        a=self.get_a()
        return a*(1-self.__e)
    
    def get_ap(self):
        a=self.get_a()
        return a*(1+self.__e)

        
er=6371000
radius=er+180000
u=7800**2*radius
v=Vector3(7800+3130,0.0,0)
r=Vector3(0,radius,0)
ob=orbit(u)
ob.set_r_v_t(r,v,0.0,u)
print(ob.get_flight_angle(math.radians(90)))
print(ob.get_ap())
