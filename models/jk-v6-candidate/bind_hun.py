import bpy,bmesh,json,math,hashlib,os,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
PBZ=ROOT.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-refined-source.blend'))
source=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
source.name='Tripo_Source_Rig'
S={b.name.removeprefix('mixamorig:'):source.matrix_world@b.head_local for b in source.data.bones}
raw=json.loads((PBZ/'models/hun-body.skel.json').read_text());bones=raw['bones']
C=Matrix.Diagonal((1.,-1.,1.,1.));G={};parents={}
for b in bones:
    q=b['q'];local=C@Matrix.LocRotScale(Vector(b['t']),Quaternion((q[3],q[0],q[1],q[2])),Vector(b['s']))@C
    parent=bones[b['parent']]['name'] if b['parent']>=0 else None
    G[b['name']]=G[parent]@local if parent else local;parents[b['name']]=parent
P={n:m.translation for n,m in G.items()}
mapping={'Hips':'pelvis','Spine':'spine_01','Spine1':'spine_03','Spine2':'spine_05','Neck':'neck_01','Head':'head'}
child={'Hips':'Spine','Spine':'Spine1','Spine1':'Spine2','Spine2':'Neck','Neck':'Head'}
for label,side in [('Left','l'),('Right','r')]:
    for a,b in [('UpLeg','thigh'),('Leg','calf'),('Foot','foot'),('ToeBase','ball'),('Shoulder','clavicle'),('Arm','upperarm'),('ForeArm','lowerarm'),('Hand','hand')]:mapping[label+a]=b+'_'+side
    for a,b in [('UpLeg','Leg'),('Leg','Foot'),('Foot','ToeBase'),('Shoulder','Arm'),('Arm','ForeArm'),('ForeArm','Hand'),('Hand','HandMiddle1')]:child[label+a]=label+b
    for f in ['Thumb','Index','Middle','Ring','Pinky']:
        for i in range(1,4):
            n=label+'Hand'+f+str(i);mapping[n]=('pinky' if f=='Pinky' else f.lower())+'_%02d_'%i+side
            if i<3:child[n]=label+'Hand'+f+str(i+1)
def affine(A,s,d):
    m=np.eye(4);m[:3,:3]=A;m[:3,3]=np.array(d)-A@np.array(s);return m
def segment(s,e,d,f,width=190):
    a=e-s;b=f-d;u=np.array(a.normalized());rotation=np.array(a.normalized().rotation_difference(b.normalized()).to_matrix())
    stretch=np.eye(3)*width+(b.length/a.length-width)*np.outer(u,u)
    return affine(rotation@stretch,s,d)
T={}
for s,d in mapping.items():
    assert d in P,(s,d)
    if s in child:T[s]=segment(S[s],S[child[s]],P[d],P[mapping[child[s]]],190 if any(w in s for w in ['Hand','Arm','Shoulder']) else 205)
    elif s=='Head':T[s]=affine(np.eye(3)*190,S[s],P[d])
    elif 'ToeBase' in s:T[s]=T[s.replace('ToeBase','Foot')]
    else:
        prev=s[:-1]+'2';A=T[prev][:3,:3];T[s]=affine(A,S[s],P[d])
# A continuous spatial cage fits the whole surface. Per-bone affine fitting caused
# separated garment islands to diverge at shoulders; source skin weights are not
# used to determine rest geometry here.
controls=[];destinations=[]
for name in ['Hips','Neck','Head']+[s+a for s in ['Left','Right'] for a in ['Arm','ForeArm','Hand','UpLeg','Leg','Foot','ToeBase']]:
    controls.append(np.array(S[name]));destinations.append(np.array(P[mapping[name]]))
for delta in [(0,0,.10),(.07,0,.07),(-.07,0,.07),(0,.06,.06),(0,-.06,.06)]:
    point=np.array(S['Head'])+np.array(delta);controls.append(point);destinations.append(T['Head'][:3,:3]@point+T['Head'][:3,3])
cs=np.array(controls);ds=np.array(destinations);poly=np.column_stack([np.ones(len(cs)),cs]);K=np.linalg.norm(cs[:,None,:]-cs[None,:,:],axis=2)
system=np.block([[K,poly],[poly.T,np.zeros((4,4))]])
coeff=np.linalg.solve(system,np.vstack([ds,np.zeros((4,3))]))
def cage(p):
    vec=np.array(p);result=np.linalg.norm(cs-vec,axis=1)@coeff[:len(cs)]+np.array([1,*vec])@coeff[len(cs):]
    # Only the neck transitions. The lower face must share the hair/head's
    # similarity transform instead of being stretched by the torso cage.
    t=float(np.clip((vec[2]-.745)/.035,0,1));t=t*t*(3-2*t)
    return result*(1-t)+(T['Head'][:3,:3]@vec+T['Head'][:3,3])*t
def torso_weights(z):
    chain=['pelvis','spine_01','spine_02','spine_03','spine_04','spine_05','neck_01','neck_02','head']
    if z<P[chain[0]].z:return {chain[0]:1.}
    for aa,bb in zip(chain,chain[1:]):
        if P[aa].z<=z<P[bb].z:
            blend=(z-P[aa].z)/(P[bb].z-P[aa].z);return {aa:1-blend,bb:blend}
    return {'head':1.}
def smooth(x):
    x=float(np.clip(x,0,1));return x*x*(3-2*x)

def apply(transform,p):
    return transform[:3,:3]@np.asarray(p)+transform[:3,3]

def frame(axis,normal):
    y=np.asarray(axis,dtype=float);y/=np.linalg.norm(y)
    z=np.asarray(normal,dtype=float);z-=y*np.dot(y,z);z/=np.linalg.norm(z)
    return np.column_stack((np.cross(y,z),y,z))

# Roll is determined by the palm, not by the shortest rotation of one digit.
# This preserves the transverse section while fitting every actual hinge.
for label,side in [('Left','l'),('Right','r')]:
    sa=np.array(S[label+'HandMiddle1']-S[label+'Hand'])
    sx=np.array(S[label+'HandIndex1']-S[label+'HandPinky1'])
    da=np.array(P['middle_01_'+side]-P['hand_'+side])
    dx=np.array(P['index_01_'+side]-P['pinky_01_'+side])
    sn=np.cross(sx,sa);dn=np.cross(dx,da)
    fs=frame(sa,sn);fd=frame(da,dn)
    palm_scales=[np.linalg.norm(dx)/np.linalg.norm(sx),np.linalg.norm(da)/np.linalg.norm(sa),190.]
    T[label+'Hand']=affine(fd@np.diag(palm_scales)@fs.T,S[label+'Hand'],P['hand_'+side])
    for finger in ['Thumb','Index','Middle','Ring','Pinky']:
        for i in [1,2,3]:
            name=label+'Hand'+finger+str(i);dest=mapping[name]
            if i<3:
                end=child[name];a=np.array(S[end]-S[name]);b=np.array(P[mapping[end]]-P[dest])
                A=frame(b,dn)@np.diag([190.,np.linalg.norm(b)/np.linalg.norm(a),190.])@frame(a,sn).T
            else:
                # The distal joint has no matching terminal bone in Hun.
                # Preserve the source terminal length at the preceding scale.
                A=T[name[:-1]+'2'][:3,:3]
            T[name]=affine(A,S[name],P[dest])

def chain_fit(p,names,blend_radius):
    """Fit segments with equal radial scales and a narrow continuous joint blend."""
    z=p[2];index=next((i for i in range(len(names)-1) if z>=S[names[i+1]].z),len(names)-1)
    result=apply(T[names[index]],p)
    for i in range(1,len(names)):
        delta=z-S[names[i]].z
        if abs(delta)<blend_radius:
            t=smooth((blend_radius-delta)/(2*blend_radius))
            result=apply(T[names[i-1]],p)*(1-t)+apply(T[names[i]],p)*t
            break
    return result

def arm_distribution(p,w):
    label='Right' if p[0]<0 else 'Left'
    values={label+'Arm':0.,label+'ForeArm':0.,label+'Hand':0.}
    for n,weight in w.items():
        if not n.startswith(label):continue
        if n==label+'Shoulder' or n==label+'Arm':values[label+'Arm']+=weight
        elif n==label+'ForeArm':values[n]+=weight
        elif n.startswith(label+'Hand'):values[label+'Hand']+=weight
    total=sum(values.values())
    return total,{n:weight/total for n,weight in values.items() if weight>0} if total else {label+'Arm':1.}

def sleeve_field(o):
    """Separate lower sleeves from the adjacent hem by surface connectivity.

    They touch in projection but are separate graph islands below the armpit.
    Harmonic interpolation makes the shoulder transition continuous.
    """
    part=o.data.attributes.get('source_component')
    if not part:return None
    points=np.array([o.matrix_world@v.co for v in o.data.vertices])
    base=np.array([part.data[v.index].value==0 for v in o.data.vertices])
    edges=np.array([e.vertices[:] for e in o.data.edges])
    edges=edges[base[edges[:,0]] & base[edges[:,1]]]
    if not len(edges):return None
    low=base & (points[:,2]<.64)
    adjacency=[[] for _ in points]
    for a,b in edges:
        if low[a] and low[b]:adjacency[a].append(b);adjacency[b].append(a)
    seeds=np.flatnonzero(low & (np.abs(points[:,0])>.14) & (points[:,2]<.56))
    found=set(map(int,seeds));queue=list(found)
    for a in queue:
        for b in adjacency[a]:
            if b not in found:found.add(int(b));queue.append(int(b))
    values=np.zeros(len(points));values[list(found)]=1.
    hard=~base | low | (np.abs(points[:,0])<.035) | (points[:,2]>.765)
    outer=base & (np.abs(points[:,0])>.11) & (points[:,2]<.765)
    hard|=outer;values[outer]=1.
    a,b=edges.T;edgew=1/np.maximum(np.linalg.norm(points[a]-points[b],axis=1),.0005)
    degree=np.bincount(a,weights=edgew,minlength=len(points))+np.bincount(b,weights=edgew,minlength=len(points))
    unknown=~hard & (degree>0)
    for iteration in range(1600):
        sums=np.bincount(a,weights=edgew*values[b],minlength=len(points))+np.bincount(b,weights=edgew*values[a],minlength=len(points))
        nextv=(values[unknown]+sums[unknown]/degree[unknown])*.5
        error=np.max(np.abs(nextv-values[unknown])) if unknown.any() else 0
        values[unknown]=nextv
        if error<1e-7:break
    print('SLEEVE_FIELD',o.name,len(found),int(unknown.sum()),iteration,float(error),flush=True)
    return values

def arm_blend(p,component,objname,w,override=None):
    region=.40<p[2]<.78 and component in [0,23]
    strength,_=arm_distribution(p,w)
    # Source skin identifies the inner sleeve separately from the adjacent hem.
    # Clean low-level cross-body leakage rather than classifying by x/z alone.
    value=(float(override) if override is not None else smooth((strength-.20)/.70)) if region else 0.
    return 1. if component==23 else value

def fitted(p,w,component,objname,arm_override=None):
    v=np.asarray(p);label='Right' if p[0]<0 else 'Left'
    if component in [2,3,6,21,22,29,34] or objname.startswith(('Halo_','Hairclip_','Hair_Gathered_')):
        return apply(T['Head'],v)
    if component in [4,5]:
        return sum((apply(T[n],v)*weight for n,weight in w.items()),np.zeros(3))
    result=cage(v)
    # The skirt and all upper-thigh decorations enter the same spatial field;
    # independent mesh islands therefore cannot acquire different rest offsets.
    arm_mix=arm_blend(p,component,objname,w,arm_override)
    leg_mix=(1-smooth((p[2]-.48)/.075))*(1-arm_mix) if component not in [0,10] else 0.
    if leg_mix:
        result=result*(1-leg_mix)+chain_fit(v,[label+n for n in ['UpLeg','Leg','Foot']],.018)*leg_mix
    if arm_mix:
        _,aw=arm_distribution(p,w)
        if component==23:aw={label+'Arm':1.}
        arm_result=sum((apply(T[n],v)*weight for n,weight in aw.items()),np.zeros(3))
        result=result*(1-arm_mix)+arm_result*arm_mix
    return result

def refine_neck_shoulders(p,result,weights,component,objname):
    """Local rest-shape/skin correction; keep all original game bone matrices."""
    p=np.asarray(p);result=np.asarray(result).copy();weights=dict(weights)
    head_piece=component in [2,3,6,21,22,29,34] or objname.startswith(('Halo_','Hairclip_','Hair_Gathered_'))
    if head_piece or (component==0 and p[2]>=.78):
        result+=np.array([0.,.6,-3.5])
        return result,weights
    if component in [1,4,5,7,9,10,12,13] or objname.startswith('Backpack_') or p[2]<=.64:
        return result,weights
    # Lower the neck's top continuously with the rigid head; shoulders lift
    # independently so the sloping shoulder line no longer lengthens the neck.
    head_mix=smooth((p[2]-.73)/.05)
    result+=np.array([0.,.6,-3.5])*head_mix
    lateral=smooth((abs(p[0])-.025)/.035)*(1-smooth((abs(p[0])-.12)/.06))
    vertical=smooth((p[2]-.64)/.065)*(1-smooth((p[2]-.75)/.035))
    shoulder=lateral*vertical
    result[2]+=4.0*shoulder
    side='r' if p[0]<0 else 'l'
    if component in [0,23]:
        # Restore proximal sleeve volume around the unchanged humerus axis.
        upper=np.array(P['upperarm_'+side]);axis=np.array(P['lowerarm_'+side])-upper
        t=float(np.dot(result-upper,axis)/np.dot(axis,axis));center=upper+axis*np.clip(t,0,1)
        radial=result-center
        volume=.18*shoulder*smooth((abs(p[0])-.055)/.045)
        result+=radial*volume
        support=.40*shoulder
        weights={n:w*(1-support) for n,w in weights.items()}
        weights['clavicle_'+side]=weights.get('clavicle_'+side,0)+support
    return result,{n:w for n,w in weights.items() if w>1e-7}

def refine_skirt(result,weights,component):
    if component!=10:return result,weights
    result=np.asarray(result).copy()
    follow=smooth((110.-result[2])/10.)
    radial=(result[:2]-np.array([0.,5.1454]))/np.array([28.**2,12.**2])
    radial/=max(np.linalg.norm(radial),1e-8)
    radial[0]*=.25
    # Prefer front/back room, keep the waist tucked under the cardigan.
    shape=smooth((106.-result[2])/10.)
    result[:2]+=radial*(2.0*shape)
    result[0]*=1-.05*shape
    left=smooth((result[0]+6.)/12.)
    strength=.55*follow
    return result,{n:w for n,w in {'pelvis':1-strength,'thigh_l':strength*left,'thigh_r':strength*(1-left)}.items() if w>1e-7}

# A measurable regression contract at the actual skeletal control points.
fit_checks=[]
for label in ['Right','Left']:
    for suffix in ['UpLeg','Leg','Foot']:
        name=label+suffix;actual=chain_fit(np.array(S[name]),[label+n for n in ['UpLeg','Leg','Foot']],.018)
        fit_checks.append({'joint':name,'miss_cm':float(np.linalg.norm(actual-P[mapping[name]]))})
    for finger in ['Thumb','Index','Middle','Ring','Pinky']:
        for i in [1,2,3]:
            name=label+'Hand'+finger+str(i)
            fit_checks.append({'joint':name,'miss_cm':float(np.linalg.norm(apply(T[name],S[name])-P[mapping[name]]))})
assert max(r['miss_cm'] for r in fit_checks)<1e-5
(ROOT/'fit-control-checks.json').write_text(json.dumps(fit_checks,indent=2),encoding='utf8')
# Create the exact game hierarchy, including all weapon and auxiliary bones.
arm=bpy.data.objects.new('Armature',bpy.data.armatures.new('Hun_Original_264'))
bpy.context.collection.objects.link(arm);bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for b in bones:
    eb=arm.data.edit_bones.new(b['name']);eb.length=4;eb.matrix=G[b['name']]
    if parents[b['name']]:eb.parent=arm.data.edit_bones[parents[b['name']]]
    eb.use_connect=False;eb.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
rows=[]
for o in meshes:
    world=o.matrix_world.copy();part=o.data.attributes.get('source_component')
    bag_marker=o.data.attributes.get('backpack_vertex') or o.data.attributes.new('backpack_vertex','INT','POINT')
    part=o.data.attributes.get('source_component')
    sleeve=sleeve_field(o)
    mapped=[];weights=[]
    for v in o.data.vertices:
        p=world@v.co
        w={o.vertex_groups[g.group].name.removeprefix('mixamorig:'):g.weight for g in v.groups if g.weight>1e-7}
        component=part.data[v.index].value if part else -1
        arm_override=sleeve[v.index] if sleeve is not None and component==0 else None
        if component in [2,3,6,21,22,29,34] or p.z>.78:w={'Head':1.}
        if component in [7,12,13] or o.name.startswith('Backpack_'):w={'Spine1':1.}
        assert w and set(w)<=set(T),(o.name,v.index,w)
        total=sum(w.values());w={n:v/total for n,v in w.items()}
        result=fitted(p,w,component,o.name,arm_override)
        mapped.append(result);dw={}
        for n,weight in w.items():dw[mapping[n]]=dw.get(mapping[n],0)+weight
        accessory=component in [2,3,6,7,12,13,21,22,29,34] or o.name.startswith(('Halo_','Hairclip_','Hair_Gathered_','Backpack_'))
        if component==10:dw={'pelvis':1.}
        if not accessory and component not in [1,4,5,9,10] and .40<p.z<.78:
            tw=torso_weights(result[2]);side='r' if p.x<0 else 'l'
            label='Right' if side=='r' else 'Left'
            arm_weight=arm_blend(p,component,o.name,w,arm_override)
            _,aw=arm_distribution(p,w)
            dw={n:weight*(1-arm_weight) for n,weight in tw.items()}
            for n,weight in aw.items():dw[mapping[n]]=dw.get(mapping[n],0)+weight*arm_weight
            dw={n:weight for n,weight in dw.items() if weight>1e-7}
        if component==0 and .755<p.z<.78:
            # Continuous attachment to the rigid lower jaw; no abrupt
            # neck/head weight boundary during a head turn.
            head_weight=smooth((p.z-.755)/.025)
            dw={n:weight*(1-head_weight) for n,weight in dw.items()}
            dw['head']=dw.get('head',0)+head_weight
            dw={n:weight for n,weight in dw.items() if weight>1e-7}
        weights.append(dw)
    if part:
        band=[v for v in o.data.vertices if part.data[v.index].value==23]
        tree=KDTree(len(band))
        for v in band:tree.insert(world@v.co,v.index)
        tree.balance()
        for v in o.data.vertices:
            if part.data[v.index].value==23:weights[v.index]={'upperarm_r':1.};continue
            if part.data[v.index].value!=0 or v.co.x>-.035 or not .60<v.co.z<.76:continue
            _,_,distance=tree.find(world@v.co);blend=smooth((.025-distance)/.015)
            if blend==0:continue
            mapped[v.index]=mapped[v.index]*(1-blend)+apply(T['RightArm'],world@v.co)*blend
            combined={bone:weight*(1-blend) for bone,weight in weights[v.index].items()}
            combined['upperarm_r']=combined.get('upperarm_r',0)+blend
            weights[v.index]={bone:weight for bone,weight in combined.items() if weight>1e-7}
    for v in o.data.vertices:
        component=part.data[v.index].value if part else -1
        mapped[v.index],weights[v.index]=refine_neck_shoulders(world@v.co,mapped[v.index],weights[v.index],component,o.name)
        mapped[v.index],weights[v.index]=refine_skirt(mapped[v.index],weights[v.index],component)
        is_bag=component in [7,12,13] or o.name.startswith('Backpack_')
        bag_marker.data[v.index].value=int(is_bag)
        if is_bag:
            center=-16.72106
            mapped[v.index][0]=center+(mapped[v.index][0]-center)*.75
    o.parent=None;o.matrix_world=Matrix.Identity(4)
    o.data.vertices.foreach_set('co',np.array(mapped).ravel());o.data.update();o.vertex_groups.clear()
    for name in sorted({n for row in weights for n in row}):
        group=o.vertex_groups.new(name=name)
        for i,row in enumerate(weights):
            if name in row:group.add([i],row[name],'REPLACE')
    for m in list(o.modifiers):
        if m.type=='ARMATURE':o.modifiers.remove(m)
    o.parent=arm;o.modifiers.new('Hun Original Skeleton','ARMATURE').object=arm
    rows.append({'name':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'used_bones':[g.name for g in o.vertex_groups]})
bpy.data.objects.remove(source,do_unlink=True)
# Merge mesh objects by material for a compact game asset. Weight groups are retained.
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join();body=bpy.context.object;body.name='Sui_JK_Hun_Body'
clean=bmesh.new();clean.from_mesh(body.data)
bad_faces=[f for f in clean.faces if f.calc_area()<1e-9]
bmesh.ops.delete(clean,geom=bad_faces,context='FACES_ONLY')
bmesh.ops.delete(clean,geom=[v for v in clean.verts if not v.link_faces],context='VERTS')
clean.to_mesh(body.data);clean.free();body.data.update()
from skirt_lining import refine_clearance_and_add_lining
lining_report=refine_clearance_and_add_lining(body)
(ROOT/'lining-report.json').write_text(json.dumps(lining_report,indent=2),encoding='utf8')
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
materials=[]
for m in body.data.materials:
    bs=m.node_tree.nodes.get('Principled BSDF');tex=next((n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
    materials.append({'slot':m.name,'base_color_linear':list(bs.inputs['Base Color'].default_value),'roughness':float(bs.inputs['Roughness'].default_value),'metallic':float(bs.inputs['Metallic'].default_value),'source_texture':tex.filepath if tex else None})
(ROOT/'game-materials.json').write_text(json.dumps(materials,indent=2),encoding='utf8')
unweighted=sum(not v.groups for v in body.data.vertices)
err=max(abs(sum(g.weight for g in v.groups)-1) for v in body.data.vertices)
assert unweighted==0 and err<1e-5
matrix_error=max(abs(arm.data.bones[n].matrix_local[i][j]-m[i][j]) for n,m in G.items() for i in range(4) for j in range(4))
assert matrix_error<.002
bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=2;bpy.context.scene.cycles.device='CPU'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=arm
fbx=ROOT/'Sui_JK_Hun_Body.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report={'bones':len(bones),'unweighted_vertices':unweighted,'max_weight_sum_error':err,'max_bone_matrix_error':matrix_error,'vertices':len(body.data.vertices),'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'fbx_sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'source_parts':rows,'no_new_cloth_or_hair_physics':True}
(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
if os.environ.get('PBZ_FIT_QUICK')=='0':
    print(json.dumps({k:v for k,v in report.items() if k!='source_parts'}));raise SystemExit(0)
scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';cam=scene.camera;light=bpy.data.objects.get('Softbox');light.location*=200;light.data.energy*=40000;light.data.size*=200
def render(name,pos,target,scale):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
render('bound-front',(0,-600,110),(0,0,110),235)
if os.environ.get('PBZ_FIT_QUICK')=='1':
    print('Quick fit preview complete');raise SystemExit(0)
render('bound-back',(0,600,110),(0,0,110),235)
render('bound-side',(-600,-80,110),(0,0,110),235)
# Diagnostic poses are previews only, never exported as game animation.
for name,angle in [('upperarm_r',-.7),('upperarm_l',.6),('lowerarm_r',-.9),('calf_l',.8)]:
    p=arm.pose.bones[name];p.rotation_mode='XYZ';p.rotation_euler[0]=angle
bpy.context.view_layer.update()
render('bound-pose-check',(-280,-600,120),(0,0,110),250)
print(json.dumps({k:v for k,v in report.items() if k!='source_parts'}))
