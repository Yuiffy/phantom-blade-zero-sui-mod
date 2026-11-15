import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(root/'private/jirai-v1/sui-jirai-motion.blend'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
names=['pelvis','spine_05','neck_01','neck_02','head','clavicle_l','upperarm_l','lowerarm_l','hand_l','middle_01_l','middle_03_l','thigh_l','calf_l','foot_l']
report={n:{'head':list(arm.data.bones[n].head_local),'parent':arm.data.bones[n].parent.name if arm.data.bones[n].parent else None} for n in names}
report['object']={'name':body.name,'matrix':list(map(list,body.matrix_world)),'vertices':len(body.data.vertices)}
report['neckbones']=[b.name for b in arm.data.bones if 'neck' in b.name.lower()]
(root/'private/dual-outfit-v1-heishang/proportion-measurements.json').write_text(json.dumps(report,indent=2))
print('PROPORTIONS',json.dumps(report))
