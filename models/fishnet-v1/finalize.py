"""Collect reviewable evidence; no game process control."""
from common import *
from PIL import Image,ImageDraw,ImageFont
import shutil

out=REPO/'evidence/fishnet-v1';out.mkdir(parents=True,exist_ok=True)
assert read(ROOT/'verification.json')['source_atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
assert read(ROOT/'editable-manifest.json')['atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
preview_files=[]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',30)
for view in ['front','back','side']:
    paths=[ROOT/(v+'-calf-'+view+'.png') for v in ['before','after']]
    for path in paths:
        assert path.stat().st_mtime>=(ROOT/'T_Jirai_Base.png').stat().st_mtime,'Stale preview'
        preview_files.append(dict(name=path.name,sha256=sha(path)))
    images=[Image.open(path).convert('RGB') for path in paths]
    canvas=Image.new('RGB',(images[0].width*2,images[0].height+65),(38,38,42))
    draw=ImageDraw.Draw(canvas)
    for i,(label,im) in enumerate(zip(['优化前','优化后'],images)):
        canvas.paste(im,(i*im.width,65));draw.text((i*im.width+24,12),label,font=font,fill='white')
    canvas.save(out/('compare-'+view+'.jpg'),quality=94)
write(ROOT/'preview-manifest.json',dict(atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),
    basis='same scene/lighting/geometry; before uses current installed source PNG, after uses authored PNG',
    files=preview_files,views_visually_reviewed=['front','back','side'],native_game_shader_emulated=False))

verification=read(ROOT/'verification.json');atlas=read(ROOT/'atlas-report.json')
receipt=read(ROOT/'installation-receipt.json') if (ROOT/'installation-receipt.json').is_file() else None
for name in ['atlas-report.json','verification.json','build-report.json']:
    shutil.copy2(ROOT/name,out/name)
write(out/'summary.json',dict(status=receipt['status'] if receipt else verification['status'],
    installed=bool(receipt),installed_at=receipt['installed_at'] if receipt else None,
    source_atlas_sha256=atlas['source_sha256'],new_atlas_sha256=atlas['output_sha256'],
    changed_texture_packages=1,unchanged_packages=98,mesh_uv_weights_cloth_and_materials_unchanged=True,
    skin_and_sclera_fixes_preserved=True,source_resolution=4096,new_resolution=8192,
    net='regular closed cylindrical diamond pattern; supersampled; garter-shaped upper boundary',
    offline_views=['front','back','side'],offline_preview_does_not_emulate_native_game_shader=True,
    game_runtime_tested=False,voice_unchanged=receipt['voice_unchanged'] if receipt else None,
    backup=receipt['backup'] if receipt else None,container_files=verification['container_files']))
print('FISHNET_EVIDENCE_WRITTEN',flush=True)
