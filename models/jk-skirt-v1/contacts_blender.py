"""Edge/surface intersections on the actual reconstructed visible skirt."""
import bpy,json,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parents[2]/'private/jk-skirt-v1';stage=sys.argv[sys.argv.index('--')+1];records=[]
for path in sorted((W/stage).glob('*-surface.npz')):
 data=np.load(path);rest=data['rest'];faces=data['faces'];mats=data['materials'];target=faces[mats==14];occluders=faces[np.isin(mats,[12,13,14,15,16])]
 sources={}
 for name,mat in [('thigh',17),('shorts',8)]:
  tri=faces[mats==mat];edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
  sources[name]=edges[(rest[edges,2].min(1)>78)&(rest[edges,2].max(1)<111)]
 samples=[]
 for fi,(p,t) in enumerate(zip(data['frames'],data['times'])):
  points=[Vector(x) for x in p];tree=BVHTree.FromPolygons(points,target.tolist(),all_triangles=True);cover=BVHTree.FromPolygons(points,occluders.tolist(),all_triangles=True);row=dict(frame=fi,time=float(t))
  cameras=[Vector(v) for v in [(0,150,110),(90,145,113),(-90,145,113),(0,-150,110),(110,-100,105),(-110,-100,105)]]
  for name,edges in sources.items():
   hits=0;visible=0
   for a,b in edges:
    delta=Vector(p[b]-p[a]);length=delta.length
    if length<.03:continue
    hit,_,face,dist=tree.ray_cast(Vector(p[a]),delta/length,length)
    if hit is not None and .015<dist<length-.015:
     hits+=1
     for camera in cameras:
      ray=hit-camera;depth=ray.length;block,_,_,distance=cover.ray_cast(camera,ray/depth,depth+.1)
      if block is not None and distance>=depth-.08:visible+=1;break
   row[name+'_edges_crossing']=hits
   row[name+'_visible_edges_crossing']=visible
  samples.append(row)
 active=[r for r in samples if r['time']>=0]
 row=dict(file=path.name,thigh_max=max(r['thigh_edges_crossing'] for r in active),thigh_sum=sum(r['thigh_edges_crossing'] for r in active),shorts_max=max(r['shorts_edges_crossing'] for r in active),shorts_sum=sum(r['shorts_edges_crossing'] for r in active),visible_thigh_max=max(r['thigh_visible_edges_crossing'] for r in active),visible_thigh_sum=sum(r['thigh_visible_edges_crossing'] for r in active),visible_lining_max=max(r['shorts_visible_edges_crossing'] for r in active),visible_lining_sum=sum(r['shorts_visible_edges_crossing'] for r in active),samples=samples)
 records.append(row);print('JK_CONTACT',stage,path.stem,'raw',row['thigh_max'],row['thigh_sum'],'visible',row['visible_thigh_max'],row['visible_thigh_sum'],'lining',row['visible_lining_max'],row['visible_lining_sum'],flush=True)
(W/stage/'contacts.json').write_text(json.dumps(dict(basis='segment intersections of upper stocking/thigh and safety shorts edges against GPU-reconstructed visible skirt; sampled synthetic motion only',records=records),indent=2))
