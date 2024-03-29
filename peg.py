from Kmath import *
from navigation import *
import Korbit
#import Ktimer
g0=9.8067

class target:
    def __init__(self):
        self.normal=Vector3(0.0,0.0,0.0)
        self.orbit=Korbit.orbit()
        self.angle=0.0
        self.radius=0.0
        self.velocity=0.0
class state:
    def __init__(self):
        self.time=0.0
        self.mass=0.0
        self.radius=Vector3(0.0,0.0,0.0)
        self.velocity=Vector3(0.0,0.0,0.0)

class previous:
    def __init__(self):
        self.rbias=Vector3(0.0,0.0,0.0)
        self.rd=Vector3(0.0,0.0,0.0)
        self.rgrav=Vector3(0.0,0.0,0.0)
        self.time=0.0
        self.v=Vector3(0.0,0.0,0.0)
        self.vgo=Vector3(0.0,0.0,0.0)
        self.tgo=0.0

class stage:
    def __init__(self):
        self.massWet=0.0
        self.massDry=0.0
        self.gLim=10.0
        self.isp=0.0
        self.thrust=0.0
        self.mode=0

class pegas:
    def __init__(self,conn):
        self.__conn=conn
        self.__vessel=conn.space_center.active_vessel
        self.__earth=conn.space_center.bodies['Earth']
        self.__u=self.__vessel.orbit.body.gravitational_parameter
        self.__reference_frame=self.__vessel.orbit.body.non_rotating_reference_frame
        self.__stages=[]
        self.__target=target()
        self.__state=state()
        self.__previous=previous()
        self.__tgo=0.0
        self.__last_stage_mass=0.0
        self.__gLim=4.5
        self.__output=(self.__vessel.flight().pitch,self.__vessel.flight().heading)
        self.__conic_extrapolation=Korbit.orbit()
        self.__mode=0 #0:standard 1:reference orbit
        self.__lambdadot=Vector3(0,0,0)
        self.__iF_=Vector3(0,0,0)
    
    def __upfg(self,n):

        stages=self.__stages
        iy = self.__target.normal
        t = self.__state.time
        m = self.__state.mass
        r = self.__state.radius
        v = self.__state.velocity

        rbias = self.__previous.rbias
        rd = self.__previous.rd
        rgrav = self.__previous.rgrav
        tp = self.__previous.time
        vprev = self.__previous.v
        vgo = self.__previous.vgo

#1
        SM=[] 
        aL=[] 
        ve=[] 
        fT=[] 
        aT=[] 
        tu=[] 
        tb=[] 
        
        for i in range(n):
    	    SM.append(stages[i].mode)
    	    aL.append(stages[i].gLim*g0)
    	    fT.append(stages[i].thrust)
    	    ve.append(stages[i].isp*g0)
    	    aT.append(fT[i] / stages[i].massWet)
    	    tu.append(ve[i]/aT[i])
    	    if stages[i].mode==0:
                tb.append((stages[i].massWet-stages[i].massDry)*ve[i]/fT[i])
    	    else:
                tb.append(ve[i]*math.log(stages[i].massWet/stages[i].massDry)/aL[i])
    #2
        dt = t-tp
        dvsensed = v-vprev
        vgo = vgo-dvsensed

    #3	
        if SM[0]==0 :
            aT[0] = fT[0] / m
        else:
            aT[0] = aL[0]
        
        tu[0] = ve[0] / aT[0]
        L = 0.0
        Li =[]
        for i in range(n-1):
    	    if SM[i]==0 :
    		    Li.append( ve[i]*math.log(tu[i]/(tu[i]-tb[i])))
    	    else:
    	    	Li.append( aL[i]*tb[i] )
    	    L = L + Li[i]
    	
    	    if L>vgo.mag() :
    		    return self.__upfg(n-1)    
                
        Li.append(vgo.mag() - L)
        tgoi = []
        for i in range(n):
            if SM[i]==0 :
                tb[i] = tu[i] * (1-math.exp((-Li[i]/ve[i])))
            else:
                tb[i] = Li[i] / aL[i]

            if i==0 :
                tgoi.append(tb[i])
            else: 
                tgoi.append(tgoi[i-1] + tb[i])
        tgo=tgoi[n-1]

    #4
        L=0.0
        J=0.0
        S=0.0
        Q=0.0
        H=0.0
        P=0.0
        
        Ji=[]
        Si=[]
        Qi=[]
        Pi=[]
        tgoi1 = 0.0
        
        for i in range(n):
    	    if i>0:
    		    tgoi1 = tgoi[i-1]

    	    if SM[i]==0:
    		    Ji.append( tu[i]*Li[i] - ve[i]*tb[i] )                                 
    		    Si.append( -Ji[i] + tb[i]*Li[i] )                                      
    		    Qi.append( Si[i]*(tu[i]+tgoi1) - 0.5*ve[i]*tb[i]**2 )                   
    		    Pi.append( Qi[i]*(tu[i]+tgoi1) - 0.5*ve[i]*tb[i]**2 * (tb[i]/3+tgoi1) )

    	    else:
    		    Ji.append( 0.5*Li[i]*tb[i] )                                      
    		    Si.append( Ji[i] )                                                
    		    Qi.append( Si[i]*(tb[i]/3+tgoi1) )                                
    		    Pi.append( (1/6)*Si[i]*(tgoi[i]**2 + 2*tgoi[i]*tgoi1 + 3*tgoi1**2) )

    	    Ji[i] = Ji[i] + Li[i]*tgoi1
    	    Si[i] = Si[i] + L*tb[i]    
    	    Qi[i] = Qi[i] + J*tb[i]    
    	    Pi[i] = Pi[i] + H*tb[i]    
    		                             
    	    L = L+Li[i]                
    	    J = J+Ji[i]                
    	    S = S+Si[i]                
    	    Q = Q+Qi[i]                
    	    P = P+Pi[i]                
    	    H = J*tgoi[i] - Q
    #5
        _lambda = vgo.unit_vector()
        if self.__previous.tgo>0:
        	rgrav = (tgo/self.__previous.tgo)**2 * rgrav
        
        rgo = rd - (r + v*tgo + rgrav)
        iz = Vector3.Cross(rd,iy).unit_vector()
        rgoxy = rgo - Vector3.Dot(iz,rgo)*iz
        rgoz = (S - Vector3.Dot(_lambda,rgoxy)) / Vector3.Dot(_lambda,iz)
        rgo = rgoxy + rgoz*iz + rbias
        lambdade = Q - S*J/L
        self.__lambdadot = (rgo - S*_lambda) / lambdade
        self.__iF_ = _lambda - self.__lambdadot*J/L
        self.__iF_ = self.__iF_.unit_vector()
        phi = Vector3.Angle(self.__iF_,_lambda)
        phidot = -phi*L/J
        vthrust = (L - 0.5*L*phi**2 - J*phi*phidot - 0.5*H*phidot**2)*_lambda
        rthrust = (S - 0.5*S*phi**2 - Q*phi*phidot - 0.5*P*phidot**2)*_lambda
        rthrust = rthrust - (S*phi + Q*phidot)*self.__lambdadot.unit_vector()
        vbias = vgo - vthrust
        rbias = rgo - rthrust
        rbias=rbias
        vbias=vbias

    #	6
    #	TODO: angle rates
        _up = r.unit_vector()
        _east = Vector3.Cross(_up,Vector3(0,1,0)).unit_vector()
        pitch = math.pi/2-Vector3.Angle(self.__iF_,_up)
        inplane =self.__iF_ - Vector3.Dot(_up,self.__iF_)*_up
        yaw = Vector3.Angle(inplane,_east)
        tangent = Vector3.Cross(_up,_east)
        if Vector3.Dot(inplane,tangent)<0 :
        	yaw = -yaw
        yaw=yaw-math.pi/2
        yaw=normalized_rad(yaw)+math.pi
        
        self.__output=(pitch,yaw)
    #	7

        ''
        rc1 = r - 0.1*rthrust - (tgo/30)*vthrust
        vc1 = v + 1.2*rthrust/tgo - 0.1*vthrust
        self.__conic_extrapolation.set_r_v(rc1.tuple3(),vc1.tuple3(),0,self.__u)
        pack = self.__conic_extrapolation.state_at_t(tgo)
        rgrav = Vector3.Tuple3(pack[0]) - rc1 - vc1*tgo
        vgrav = Vector3.Tuple3(pack[1]) - vc1

        #print(rbias)
        #print(vbias)
        #print('\n')
      
    #	8
        rp = r + v*tgo + rgrav + rthrust
        rp = rp - Vector3.Dot(rp,iy)*iy

        vd=Vector3(0.0,0.0,0.0)
        if self.__mode==0:
            gamma = self.__target.angle
            rdval = self.__target.radius
            vdval = self.__target.velocity
            rd = rdval*rp.unit_vector()
            ix = rd.unit_vector()
            iz = Vector3.Cross(ix,iy)
            vd=(iz*math.cos(gamma)+ix*math.sin(gamma))*vdval
        elif self.__mode==1:
            pe=Vector3.Tuple3(self.__target.orbit.pe_vector())
            f=Vector3.Angle(pe,rp)
            if Vector3.Dot(Vector3.Cross(pe,rp),self.__target.normal)>0:
                f=-f
            target_state= self.__target.orbit.state_at_f(f)

            rd=Vector3.Tuple3(target_state[0])
            vd=Vector3.Tuple3(target_state[1])
        else:
            print('pegas error:unkown work mode')

        vgo = vd - v - vgrav + vbias

        self.__previous.rbias = rbias
        self.__previous.rd    = rd   
        self.__previous.rgrav = rgrav
        self.__previous.time  = self.__state.time   
        self.__previous.v     = self.__state.velocity
        self.__previous.vgo   = vgo 
        self.__previous.tgo=tgo
        self.__tgo=self.__previous.tgo

    def set_std_target(self,inc,lan,radius,velocity,angle=0.0):
        self.__mode=0
        self.__target.angle=angle
        self.__target.normal=target_normal_vector(self.__conn,self.__earth,inc,lan,self.__reference_frame)
        self.__target.radius=radius
        self.__target.velocity=velocity

        r=Vector3.Tuple3(self.__vessel.position(self.__reference_frame))
        v=Vector3.Tuple3(self.__vessel.velocity(self.__reference_frame))
        q=Quaternion.PivotRad(self.__target.normal,math.radians(1))
        rd=q.rotate(r)
        vd=Vector3.Cross(rd,self.__target.normal).unit_vector()*velocity
        self.__previous.rd    = rd   
        self.__previous.time  = self.__conn.space_center.ut   
        self.__previous.v     = v
        self.__previous.vgo   = vd-v
        ''
        self.__state.time=self.__conn.space_center.ut
        self.__state.mass=self.__vessel.mass
        self.__state.radius=Vector3.Tuple3(self.__vessel.position(self.__reference_frame))
        self.__state.velocity=Vector3.Tuple3(self.__vessel.velocity(self.__reference_frame))

    def set_ref_target(self,pe,ap,inc,lan,aop):
        self.__mode=1
        sem=0.5*(pe+ap)
        ecc=0.5*(ap-pe)/sem
        self.__target.normal=target_normal_vector(self.__conn,self.__earth,inc,lan,self.__reference_frame)
        self.__target.orbit.set_element(sem,ecc,inc,lan,aop,0.0,0.0,self.__u)
        r=Vector3.Tuple3(self.__vessel.position(self.__reference_frame))
        v=Vector3.Tuple3(self.__vessel.velocity(self.__reference_frame))
        q=Quaternion.PivotRad(self.__target.normal,math.radians(20))
        rd=q.rotate(r)
        vd=Vector3.Cross(rd,self.__target.normal).unit_vector()*v.mag()
        self.__previous.rd    = rd   
        self.__previous.time  = self.__conn.space_center.ut   
        self.__previous.v     = v
        self.__previous.vgo   = vd-v
        ''
        self.__state.time=self.__conn.space_center.ut
        self.__state.mass=self.__vessel.mass
        self.__state.radius=Vector3.Tuple3(self.__vessel.position(self.__reference_frame))
        self.__state.velocity=Vector3.Tuple3(self.__vessel.velocity(self.__reference_frame))
    def set_radius_speed_target(self,radius,velocity,angle=0.0):
        self.__mode=0
        self.__target.angle=angle
        self.__state.radius=Vector3.Tuple3(self.__vessel.position(self.__reference_frame))
        self.__state.velocity=Vector3.Tuple3(self.__vessel.velocity(self.__reference_frame))
        self.__target.normal=Vector3.Cross(self.__state.velocity,self.__state.radius).unit_vector()
        self.__target.radius=radius
        self.__target.velocity=velocity

        r=Vector3.Tuple3(self.__vessel.position(self.__reference_frame))
        v=Vector3.Tuple3(self.__vessel.velocity(self.__reference_frame))
        q=Quaternion.PivotRad(self.__target.normal,math.radians(1))
        rd=q.rotate(r)
        vd=Vector3.Cross(rd,self.__target.normal).unit_vector()*velocity
        self.__previous.rd    = rd   
        self.__previous.time  = self.__conn.space_center.ut   
        self.__previous.v     = v
        self.__previous.vgo   = vd-v
        self.__state.time=self.__conn.space_center.ut
        self.__state.mass=self.__vessel.mass
    def __add_stage(self,massWet,massDry,thrust,isp,gLim,mode):
        _stage=stage()
        _stage.massWet=massWet
        _stage.massDry=massDry
        _stage.gLim=gLim
        _stage.isp=isp
        _stage.thrust=thrust
        _stage.mode=mode
        self.__stages.append(_stage)

    def add_stage(self,massWet,massDry,thrust,isp,gLim=4.5):
        _stage=stage()
        self.__stages.reverse()
        last_stage_mass=self.__last_stage_mass
            
        if thrust==0 or isp==0 or massWet==massDry:
            self.__last_stage_mass=last_stage_mass+massWet
            return None
      
        mass_tmp=thrust/(gLim*g0)
        if mass_tmp<=massDry+last_stage_mass:
            self.__add_stage(massWet+last_stage_mass,massDry+last_stage_mass,thrust,isp,gLim,0)
        elif mass_tmp>=massWet+last_stage_mass:
            self.__add_stage(massWet+last_stage_mass,massDry+last_stage_mass,thrust,isp,gLim,1)
        else:
            self.__add_stage(mass_tmp,massDry+last_stage_mass,thrust,isp,gLim,1)
            self.__add_stage(massWet+last_stage_mass,mass_tmp,thrust,isp,gLim,0)
        self.__last_stage_mass=last_stage_mass+massWet
        self.__stages.reverse()

    def slerp(self):
        self.__state.time=self.__conn.space_center.ut
        self.__state.mass=self.__vessel.mass
        self.__state.radius=Vector3.Tuple3(self.__vessel.position(self.__reference_frame))
        self.__state.velocity=Vector3.Tuple3(self.__vessel.velocity(self.__reference_frame))
        r = self.__state.radius

        dt=self.__conn.space_center.ut-self.__previous.time
        iF_ = self.__iF_ + self.__lambdadot*dt
        iF_ = iF_.unit_vector()
        
        self.__tgo=self.__previous.tgo-dt
    #	6
    #	TODO: angle rates
        _up = r.unit_vector()
        _east = Vector3.Cross(_up,Vector3(0,1,0)).unit_vector()
        pitch = math.pi/2-Vector3.Angle(iF_,_up)
        inplane =iF_- Vector3.Dot(_up,iF_)*_up
        yaw = Vector3.Angle(inplane,_east)
        tangent = Vector3.Cross(_up,_east)
        if Vector3.Dot(inplane,tangent)<0 :
        	yaw = -yaw
        yaw=yaw-math.pi/2
        yaw=normalized_rad(yaw)+math.pi
        self.__output=(pitch,yaw)        

    def update(self):
        self.__state.time=self.__conn.space_center.ut
        self.__state.mass=self.__vessel.mass
        self.__state.radius=Vector3.Tuple3(self.__vessel.position(self.__reference_frame))
        self.__state.velocity=Vector3.Tuple3(self.__vessel.velocity(self.__reference_frame))
 
        vessel=self.__vessel
        n=len(self.__stages)
        self.__stages[0].massWet=self.__state.mass
        if self.__state.mass<=self.__stages[0].massDry:
            self.__stages.pop(0)
            vessel.control.throttle=1.0
            #self.__throttle_bias.clear()
            return None
        
        '''
        if self.__stages[0].mode!=0:
            acc=vessel.thrust/max(vessel.mass,0.1)
            dacc=acc-g0*self.__stages[0].gLim
            dacc=max(-1,min(1,dacc))
            vessel.control.throttle = 1.0-self.__throttle_bias.integral(0.05*dacc)
        '''

        last_tgo=self.__previous.tgo
        self.__upfg(n)
        #if abs(last_tgo-self.__previous.tgo)>1:
        #   return None
        return self.__output

    def update_stages(self,thrustK=1.0):
        self.__last_stage_mass=0.0
        self.__stages=[]
        stages=get_stages(self.__vessel.parts.root)
        for i in stages:
            self.add_stage(i[0],i[1],i[2]*thrustK,i[3],self.__gLim)

    def time_to_go(self):
            return self.__tgo
    
    def __time_to_stage(self,stage):
        if stage.mode==0:
            dm=stage.thrust/(stage.isp*g0)
            return (stage.massWet-stage.massDry)/dm     
        else:
            dv=stage.isp*math.log(stage.massWet/stage.massDry)
            return dv/stage.gLim

    def time_to_stage(self):
        stage=self.__stages[0]
        ret=self.__time_to_stage(stage)
        if len(self.__stages)>1:
            if self.__stages[1].massWet==stage.massDry:
                ret=ret+self.__time_to_stage(self.__stages[1])
        return ret

    def stages_num(self):
        return len(self.__stages)

    def angle_to_rd(self):
        return Vector3.Angle(self.__previous.rd,self.__state.radius)
    
    def rd_position(self):
        pos=self.__previous.rd.tuple3()
        ref=self.__reference_frame
        body=self.__vessel.orbit.body
        turn_angle=math.degrees(body.rotational_speed*self.__previous.tgo)
        return (body.longitude_at_position(pos,ref)-turn_angle,body.latitude_at_position(pos,ref))

    def set_max_g(self,g):
        self.__gLim=g
   
    def vehicle_info(self):
        for i in self.__stages:
            print('wet mass:%f dry mass:%f thurst:%f isp:%f'%(i.massWet,i.massDry,i.thrust,i.isp))