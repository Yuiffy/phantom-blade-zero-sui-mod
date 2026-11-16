"""Bundle the verified local candidate and encode its real sampled preview."""
from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(__file__).resolve().parents[2]/'private/jirai-v1';W=R/'variant';O=R/'review-r4-wings';C=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=sha(R/'Sui_Jirai_Hun_Body.fbx')
assert read(W/'verification.json')['status']=='independent-container-semantics-passed'
assert read(W/'wing-surface-verification.json')['passed'] and read(W/'wing-surface-verification.json')['fbx_sha256']==source
assert read(W/'simulation-validation.json')['fbx_sha256']==source
assert read(W/'shoulder-retarget-verification.json')['passed'] and read(W/'shoulder-retarget-verification.json')['fbx_sha256']==source
fps=1/(10*read(O/'motion-source.json')['dt']);ff='D:/tools/ffmpeg/bin/ffmpeg.exe'
common=[ff,'-y','-v','error','-threads','2','-filter_threads','1','-filter_complex_threads','1','-framerate',str(fps),'-i',str(O/'motion-frames/%03d.png')]
for args in [
 ['-filter_complex','[0:v]split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a','-loop','0',str(O/'wing-motion.gif')],
 ['-vf','fps=30','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(O/'wing-motion.mp4')]]:
 subprocess.run(common+args,check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
candidate=O/'candidate';candidate.mkdir(exist_ok=True)
build=read(W/'build-report.json')
for row in build['container_files']:
 p=Path(row['path']);assert sha(p)==row['sha256'];shutil.copy2(p,candidate/p.name)
for name in ['verification.json','simulation-validation.json','cloth-assets-verification.json','cloth-native-verification.json','wing-surface-verification.json','render-deformation-review.json','shoulder-retarget-verification.json','editor-reload-verification.json']:
 shutil.copy2(W/name,O/name)
shutil.copy2(W/'shoulder-rig/independent-verification.json',O/'shoulder-native-verification.json')
shutil.copy2(C/'WINGS-R4.md',O/'制作说明.md')
mods=Path('F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods');before=read(R/'installed-observed-r4.json')
after=[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(mods.iterdir()) if p.is_file()]
(O/'installed-audit.json').write_text(json.dumps({'unchanged_since_r4_observation':before==after,'files':after,'this_pipeline_installs_nothing':True},indent=2))
(O/'说明.txt').write_text('地雷岁 R4 本地候选，尚未安装、尚未游戏实测。\n棉花翅膀由助手额外添加，用户接受暂时保留；独立对象 Optional_Cotton_Wings 可完整移除。\n动态预览来自实际离线 Chaos 解算及成品 GPU 映射，不是游戏录屏。\n随动作小幅回弹，静止会收敛；并非持续循环悬浮动画。\n候选和现用 JK 占用同一个黑伤（逃亡）服装槽位，不能叠装。现用文件未被本流程更改。\n高角度腋下形变、游戏内骨骼动画和战斗碰撞仍须检查。\n',encoding='utf8')
files=[p for p in O.iterdir() if p.is_file() and p.name!='manifest.json']+list(candidate.iterdir())
(O/'manifest.json').write_text(json.dumps({'status':'offline-verified-candidate-not-installed','fbx_sha256':source,'packages':44,'game_runtime_tested':False,'files':[{'path':p.relative_to(O).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]},indent=2))
print('R4_REVIEW_READY_NOT_INSTALLED',len(files),'files')
