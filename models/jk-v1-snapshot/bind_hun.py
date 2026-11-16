import bpy,bmesh,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parent
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
    t=float(np.clip((vec[2]-.755)/.055,0,1));t=t*t*(3-2*t)
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
    mapped=[];weights=[]
    for v in o.data.vertices:
        p=world@v.co
        w={o.vertex_groups[g.group].name.removeprefix('mixamorig:'):g.weight for g in v.groups if g.weight>1e-7}
        component=part.data[v.index].value if part else -1
        if component in [2,3,6,21,22,29,34] or p.z>.79:w={'Head':1.}
        if component in [7,12,13] or o.name.startswith('Backpack_'):w={'Spine1':1.}
        assert w and set(w)<=set(T),(o.name,v.index,w)
        total=sum(w.values());w={n:v/total for n,v in w.items()}
        result=cage(p)
        if component in [2,3,6,21,22,29,34] or o.name.startswith(('Halo_','Hairclip_','Hair_Gathered_')):result=T['Head'][:3,:3]@np.array(p)+T['Head'][:3,3]
        mapped.append(result);dw={}
        for n,weight in w.items():dw[mapping[n]]=dw.get(mapping[n],0)+weight
        accessory=component in [2,3,6,7,12,13,21,22,29,34] or o.name.startswith(('Halo_','Hairclip_','Hair_Gathered_','Backpack_'))
        if not accessory and component not in [4,5] and .49<p.z<.79:
            tw=torso_weights(result[2]);side='r' if p.x<0 else 'l'
            threshold=.075+max(0,.75-p.z)*.14
            arm_weight=smooth((abs(p.x)-threshold)/.045)
            lower=smooth((.66-p.z)/.075)
            dw={n:weight*(1-arm_weight) for n,weight in tw.items()}
            dw['upperarm_'+side]=(1-lower)*arm_weight;dw['lowerarm_'+side]=lower*arm_weight
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
            _,_,distance=tree.find(world@v.co);blend=smooth((.055-distance)/.030)
            if blend==0:continue
            combined={bone:weight*(1-blend) for bone,weight in weights[v.index].items()}
            combined['upperarm_r']=combined.get('upperarm_r',0)+blend
            weights[v.index]={bone:weight for bone,weight in combined.items() if weight>1e-7}
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
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=arm
fbx=ROOT/'Sui_JK_Hun_Body.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report={'bones':len(bones),'unweighted_vertices':unweighted,'max_weight_sum_error':err,'max_bone_matrix_error':matrix_error,'vertices':len(body.data.vertices),'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'fbx_sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'source_parts':rows,'no_new_cloth_or_hair_physics':True}
(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
scene=bpy.context.scene;cam=scene.camera;light=bpy.data.objects.get('Softbox');light.location*=200;light.data.energy*=40000;light.data.size*=200
def render(name,pos,target,scale):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
render('bound-front',(0,-600,110),(0,0,110),235)
render('bound-back',(0,600,110),(0,0,110),235)
render('bound-side',(-600,-80,110),(0,0,110),235)
# Diagnostic poses are previews only, never exported as game animation.
for name,angle in [('upperarm_r',-.7),('upperarm_l',.6),('lowerarm_r',-.9),('calf_l',.8)]:
    p=arm.pose.bones[name];p.rotation_mode='XYZ';p.rotation_euler[0]=angle
bpy.context.view_layer.update()
render('bound-pose-check',(-280,-600,120),(0,0,110),250)
print(json.dumps({k:v for k,v in report.items() if k!='source_parts'}))
