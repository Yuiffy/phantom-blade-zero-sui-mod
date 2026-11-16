"""Non-destructive source refinement; original FBX and texture remain untouched."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'review-source.blend'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
comps=json.loads((ROOT/'components.json').read_text())
part=body.data.attributes.new('source_component','INT','POINT')
for component in comps:
    for index in component['indices']:part.data[index].value=component['id']
remove=[c['id'] for c in comps if c['id'] in (8,24,28,30) or c['min'][2]>.923]
# Scalp belongs to a larger component with a low bounding-box minimum.
ids={v for c in comps if c['id'] in remove for v in c['indices']}
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.verts[i] for i in ids],context='VERTS');bm.to_mesh(body.data);bm.free()
body.name='Sui_JK_Base';body.data.update()
base=body.data.materials[0];base.name='MI_JK_Base'
# Keep the editable master physically shaded; review lighting is separate.
bs=next(n for n in base.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Emission Strength'].default_value=.2
added=[]
def material(name,color,metal=0,rough=.55):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m
gold=material('MI_JK_Gold',(.83,.49,.16),.45,.32)
pink=material('MI_JK_Pink',(.67,.028,.16))
lightpink=material('MI_JK_PinkLight',(.95,.12,.32))
darkpink=material('MI_JK_PinkSeam',(.32,.009,.065))
cat=material('MI_JK_Cat',(.025,.012,.018))
silver=material('MI_JK_Silver',(.7,.72,.76),.65,.35)
hairline=material('MI_JK_HairGroove',(.75,.67,.74),0,.8)
hairpink=material('MI_JK_HairRose',(.95,.30,.50),0,.8)
def finish(o,name,mat,bone='mixamorig:Head'):
    o.name=name
    if o.type!='MESH':
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
    o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE')
    world=o.matrix_world.copy();o.parent=rig;o.matrix_world=world
    o.modifiers.new('Source Skin','ARMATURE').object=rig
    added.append(o);return o
def tube(name,points,radius,mat,bone='mixamorig:Head',closed=False):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2;d.bevel_depth=radius;d.bevel_resolution=2;d.use_fill_caps=True
    s=d.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=closed
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);return finish(o,name,mat,bone)
def box(name,center,size,mat,bevel=.002,bone='mixamorig:Head'):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=o.modifiers.new('Rounded edges','BEVEL');mod.width=bevel;mod.segments=3
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(o,name,mat,bone)
def lens(name,start,end,width,normal,mat,bone='mixamorig:Head'):
    start,end,n=Vector(start),Vector(end),Vector(normal).normalized();axis=(end-start);side=axis.normalized().cross(n).normalized()
    vertices=[];faces=[]
    for i in range(9):
        t=i/8;center=start+axis*t;w=width*math.sin(math.pi*t)
        vertices.extend([center-side*w,center+n*w*.32,center+side*w,center-n*w*.24])
    for i in range(8):
        for j in range(4):faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return finish(o,name,mat,bone)
# One closed planar ellipse in 3D. No chord and no disconnected back half.
C=Vector((-.055,0,.987));U=Vector((.62,-.62,.48)).normalized();V=Vector((.707,.707,0)).normalized();N=U.cross(V).normalized();A=.075;B=.026
def ring(t):return C+U*(A*math.cos(t))+V*(B*math.sin(t))
tube('Halo_Continuous_Ring',[ring(i*2*math.pi/192) for i in range(192)],.0011,gold,closed=True)
for i in range(13):
    t=.28+i*(math.pi-.56)/12
    p=ring(t);tangent=(-U*A*math.sin(t)+V*B*math.cos(t)).normalized();outward=(U*math.cos(t)+V*math.sin(t)).normalized()
    for sign in (-1,1):
        direction=(tangent*.60+outward*(sign*.8)).normalized()
        lens('Halo_Laurel_%02d_%s'%(i,sign),p,p+direction*.0105,.0025,N,gold)
for sign in (-1,1):
    tip=C+U*A*sign
    lens('Halo_Tip_'+str(sign),tip-U*sign*.007,tip+U*sign*.008,.0026,N,gold)
# Project the clips onto the existing fringe, avoiding the removed floating islands.
worldverts=[body.matrix_world@v.co for v in body.data.vertices]
bvh=BVHTree.FromPolygons(worldverts,[list(p.vertices) for p in body.data.polygons])
def front(x,z,offset=.0015):
    hit=bvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)))
    assert hit[0] is not None,(x,z)
    return Vector((x,hit[0].y-offset,z))
def front_line(name,a,b,r,mat):
    tube(name,[front(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for t in [i/12 for i in range(13)]],r,mat)
for z in [.870,.874]:
    front_line('Hairclip_Pink_Bar',(-.032,z),(-.013,z+.001),.0018,pink)
front_line('Hairclip_Gold_Cross_A',(-.030,.857),(-.014,.865),.00105,gold)
front_line('Hairclip_Gold_Cross_B',(-.030,.866),(-.014,.856),.00105,gold)
# A small black cat-head silhouette, aligned to the left fringe.
cc=front(.032,.871,.0023)
outline=[(-.009,-.002),(-.009,.005),(-.006,.008),(-.003,.004),(.003,.004),(.006,.008),(.009,.005),(.009,-.002),(.005,-.005),(-.005,-.005)]
vs=[(cc.x+x,cc.y+y,cc.z+z) for y in [-.001,.001] for x,z in outline];nn=len(outline)
faces=[tuple(range(nn-1,-1,-1)),tuple(range(nn,2*nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
me=bpy.data.meshes.new('Cat badge');me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new('Hairclip_Cat',me);bpy.context.collection.objects.link(o);finish(o,'Hairclip_Cat',cat)
for x in [-.003,.003]:
    lens('Hairclip_Cat_Eye',cc+Vector((x,-.0025,-.0005)),cc+Vector((x,-.0025,.001)),.0007,(0,-1,0),pink)
# Backpack front-facing outer panel: a centered pocket, zipper, heart row and handle.
bagbone='mixamorig:Spine2';cx=-.051;surface=.136
box('Backpack_Front_Pocket',(cx,surface+.005,.605),(.133,.014,.094),pink,.010,bagbone)
def rounded_rectangle(cx,y,cz,w,h,r):
    pts=[]
    for ox,oz,t0 in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(9):
            a=math.radians(t0+j*90/8);pts.append((cx+ox+r*math.cos(a),y,cz+oz+r*math.sin(a)))
    return pts
tube('Backpack_Pocket_Piping',rounded_rectangle(cx,surface+.013,.605,.128,.088,.01),.0011,darkpink,bagbone,True)
tube('Backpack_Zipper',[(cx-.055,surface+.014,.639),(cx+.055,surface+.014,.639)],.0008,silver,bagbone)
tube('Backpack_Zipper_Pull',[(cx-.048,surface+.016,.638),(cx-.048,surface+.018,.627),(cx-.044,surface+.018,.627),(cx-.044,surface+.016,.637)],.0008,gold,bagbone,True)
def heart(name,x,y,z,size,mat):
    pts=[]
    for i in range(48):
        t=i*2*math.pi/48
        pts.append((x+size*math.sin(t)**3,y,z+size*(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/16))
    tube(name,pts,.00085,mat,bagbone,True)
for i in range(6):heart('Backpack_Heart_Trim',cx+(i-2.5)*.019,surface+.001,.687,.009,lightpink)
heart('Backpack_Heart_Badge',cx,surface-.004,.711,.0045,cat)
tube('Backpack_Handle',[(cx+.023*math.cos(t),.080,.731+.022*math.sin(t)) for t in [i*math.pi/40 for i in range(41)]],.0035,darkpink,bagbone)
# The unused shoulder strap hangs on the opposite side, as in the approved rear view.
tube('Backpack_Unused_Strap',[(.011,.049,.717),(.027,.044,.692),(.039,.037,.638),(.044,.026,.581),(.035,.016,.555),(.019,.020,.557),(.014,.031,.580)],.0042,pink,bagbone)
box('Backpack_Strap_Buckle',(.039,.028,.603),(.011,.007,.014),silver,.0012,bagbone)
# Follow the rear scalp surface with fine combed strand lines towards the ponytail tie.
for j in range(5):
    start=Vector((.053-j*.020,.0,.873+j*.010));end=Vector((-.060,.0,.899))
    pts=[]
    for i in range(33):
        t=i/32;x=start.x*(1-t)+end.x*t;z=start.z*(1-t)+end.z*t-.022*math.sin(math.pi*t)
        hit=bvh.ray_cast(Vector((x,.4,z)),Vector((0,-1,0)))
        if hit[0] is not None and hit[0].y>-.025:pts.append(hit[0]+Vector((0,.00065,0)))
    if len(pts)>4:tube('Hair_Gathered_Strand_%02d'%j,pts,.00025,hairline)
# Normalize all added object transforms without disturbing imported weights.
for o in added:
    M=o.matrix_world.copy();o.parent=None
    o.data.transform(M);o.matrix_world=Matrix.Identity(4);o.parent=rig
    if o.name.startswith('Backpack_Front_Pocket'):
        grid=bmesh.new();grid.from_mesh(o.data)
        bmesh.ops.subdivide_edges(grid,edges=list(grid.edges),cuts=4,use_grid_fill=True)
        grid.to_mesh(o.data);grid.free()
    if o.name.startswith(('Backpack_Front_Pocket','Backpack_Pocket_Piping','Backpack_Zipper','Backpack_Heart_')):
        for v in o.data.vertices:
            hit=bvh.ray_cast(Vector((v.co.x,.4,v.co.z)),Vector((0,-1,0)))
            assert hit[0] is not None,o.name
            v.co.y=hit[0].y+(v.co.y-surface)+.002
    # New geometry receives explicit UVs even for constant-color materials.
    if not o.data.uv_layers:
        uv=o.data.uv_layers.new(name='UVMap')
        for loop in o.data.loops:uv.data[loop.index].uv=(o.data.vertices[loop.vertex_index].co.x+.5,o.data.vertices[loop.vertex_index].co.z)
    clean=bmesh.new();clean.from_mesh(o.data)
    bmesh.ops.remove_doubles(clean,verts=list(clean.verts),dist=1e-8)
    bmesh.ops.dissolve_degenerate(clean,edges=list(clean.edges),dist=1e-8)
    bmesh.ops.triangulate(clean,faces=list(clean.faces))
    bmesh.ops.recalc_face_normals(clean,faces=list(clean.faces))
    clean.to_mesh(o.data);clean.free();o.data.update()
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
bpy.context.scene.camera.data.ortho_scale=1.17
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-refined-source.blend'),compress=True)
report={'source_triangles':51214,'removed_component_ids':remove,'removed_vertices':len(ids),'added_mesh_objects':len(added),'triangles':sum(len(p.vertices)-2 for o in [body]+added for p in o.data.polygons),'source_rig_bones':len(rig.data.bones),'changes':['Rebuilt continuous tilted gold halo and laurel details','Projected pink and crossed gold hairclips onto fringe','Rebuilt cat hairclip silhouette','Added backpack pocket, zipper, heart trim, handle and loose strap','Added rear combed hair strand lines'],'limitations':['No new facial blendshapes','Cloth and hair physics not added; game binding pending']}
(ROOT/'refinement-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
scene=bpy.context.scene;cam=scene.camera
def render(name,position,target,scale):
    cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
render('after-head',(0,-3,.905),(0,0,.905),.35)
render('after-side',(-3,-.15,.76),(0,0,.76),.72)
render('after-back',(0,3,.55),(0,0,.55),1.17)
render('after-front',(0,-3,.55),(0,0,.55),1.17)
print(json.dumps(report))
