"""Preserve six flat color/response regions in one native cloth render section."""
from pathlib import Path
import json,hashlib
from PIL import Image
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v1'
spec=json.loads((R.parents[2]/'variants/new-jk-v11/material-spec.json').read_text())
tex={r['package']:r for r in spec['textures']};rows=[r for r in spec['materials'] if r['slot'].startswith('MI_JK_Charm_')]
assert len(rows)==6
out=R/'textures';out.mkdir(exist_ok=True);records=[];images={k:Image.new('RGBA',(512,256)) for k in ['Albedo','Mix']}
for i,row in enumerate(rows):
 x,y=(i%4)*128,(i//4)*128;colors={}
 for kind in images:
  im=Image.open(tex[row['textures'][kind]]['path']).convert('RGBA');colors[kind]=im.getpixel((0,0))
  assert im.getcolors(2)==[(im.width*im.height,colors[kind])]
  images[kind].paste(colors[kind],(x,y,x+128,y+128))
 records.append({'old_slot':row['slot'],'uv':[(x+64)/512,1-(y+64)/256],'colors':colors})
packages={}
for kind,im in images.items():
 name='T_JK_CharmAtlas' if kind=='Albedo' else 'T_JK_ARM_CharmAtlas';p=out/(name+'.png');im.save(p)
 package='/HuaShira/Mods/SuiPBZ/JKVT/'+name;packages[kind]=package
 spec['textures'].append({'name':name,'kind':'albedo' if kind=='Albedo' else 'mask','path':str(p),'package':package,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
new=dict(rows[0],slot='MI_JK_CharmAtlas',textures={'Albedo':packages['Albedo'],'Normal':rows[0]['textures']['Normal'],'Mix':packages['Mix']})
spec['materials']=[r for r in spec['materials'] if r not in rows]+[new]
# Preserve only textures used by final materials, removing now-unused flat colors.
used={p for row in spec['materials'] for p in row['textures'].values()};spec['textures']=[r for r in spec['textures'] if r['package'] in used]
(W/'material-spec.json').write_text(json.dumps(spec,indent=2))
(R/'charm-atlas.json').write_text(json.dumps({'new_slot':new['slot'],'regions':records,'albedo':str(out/'T_JK_CharmAtlas.png'),'mask':str(out/'T_JK_ARM_CharmAtlas.png'),'geometry_and_skin_unchanged':True},indent=2))
cloth=json.loads((R/'cloth-spec.json').read_text())
for row in cloth:
 if row['name']=='CA_Sui_Charm':row.update(slot=new['slot'],additional_render_slots=[])
(R/'cloth-spec.json').write_text(json.dumps(cloth,indent=2))
print('CHARM_ATLAS',len(spec['materials']),'materials',len(spec['textures']),'textures')
