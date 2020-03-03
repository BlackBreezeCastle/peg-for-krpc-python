import krpc

def find_resource(parts,name):
    ret=0.0
    for i in parts:
        for r in i.resources.all:
            if r.name==name:
                ret=ret+r.amount*r.density
    return ret

def traverse_engine(parts):
    engines = [e for e in parts if e.engine!=None]
    res=[]
    for e in engines:
        fuel=0.0
        for p in e.engine.propellants:
            fuel=fuel+find_resource(parts,p.name)
        res.append((e.engine,fuel))
    return res

def all_descendants(root):
    ret=[]
    stack_parts=[root]
    while stack_parts:
        part = stack_parts.pop()
        ret.append(part)
        for i in part.children:
            stack_parts.append(i)
    return ret

def traverse_stage(root):
    stack_parts=[root]
    decoupler=None
    ret=[None,[]]
    while stack_parts:
        part = stack_parts.pop()
        ret[1].append(part)
        for child in part.children:
            if child.decoupler==None :
                stack_parts.append(child)
            else:
                tmp_parts=all_descendants(child)
                engines = [e for e in tmp_parts if e.engine!=None]
                if len(engines)==0:
                    stack_parts.append(child)
                else:
                    if decoupler==None:
                        decoupler=child
                    elif decoupler.stage<child.stage:
                        stack_parts.append(decoupler)
                        decoupler=child
                    else:
                        stack_parts.append(child)
    ret[0]=decoupler
    return ret


def get_stages(root):
    ret=[]
    next=root
    while next:
        isp=0.0
        thrust=0.0
        mass_wet=0.0
        tmp=traverse_stage(next)
        next=tmp[0]
        parts=tmp[1]
        for i in parts:
            mass_wet=mass_wet+i.mass
        mass_dry=mass_wet
        engines=traverse_engine(parts)
        for e in engines:
            if e[1]>mass_wet*0.02:
                thrust=thrust+e[0].max_vacuum_thrust
                isp=e[0].vacuum_specific_impulse
                mass_dry=mass_wet-e[1]
        ret.append([mass_wet,mass_dry,thrust,isp])
    return ret
