"""Receipt-bound replacement of the rejected Polish1, with automatic recovery."""
from common import *
import datetime,shutil

def exited():
 result=subprocess.run(['pwsh','-NoLogo','-NoProfile','-NonInteractive','-Command',"@(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' }).Count"],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert result.returncode==0 and result.stdout.decode().strip()=='0','PBZ is running; exit the game before installation'

def main(apply=False,rollback=False):
 exited()
 if rollback:
  receipt=read(ROOT/'installation-receipt.json');assert snapshot()==receipt['after']
  for row in receipt['removed']:assert sha(Path(receipt['backup'])/row['name'])==row['sha256']
  if not apply:print('HYBRID_ROLLBACK_PREFLIGHT_PASSED');return
  dest=ROOT/('rollback-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));dest.mkdir()
  for row in receipt['added']:shutil.move(str(MODS/row['name']),str(dest/row['name']))
  for row in receipt['removed']:shutil.copy2(Path(receipt['backup'])/row['name'],MODS/row['name'])
  assert snapshot()==receipt['before'];write(ROOT/'rollback-receipt.json',dict(restored=True,files=snapshot()));print('HYBRID_ROLLED_BACK');return
 assert_baseline();gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');mount=read(ROOT/'mount-verification.json');visual=read(ROOT/'visual-review.json')
 assert gate['passed'] and gate['package_count']==3 and gate['bounded_native_changes_exact'] and gate['skeleton_sections_cloth_physics_exact'] and gate['copied_weights_readback_exact']
 assert geometry['passed'] and geometry['final_container_readback'] and mount['passed'] and mount['directory_order_independent'] and visual['reviewed']
 assert gate['native_render_sha256']==geometry['native_render_sha256']==mount['native_render_sha256']==visual['native_render_sha256']==sha(ROOT/'final-render.npz')
 assert gate['source_atlas_sha256']==geometry['source_atlas_sha256']==mount['source_atlas_sha256']==visual['source_atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
 for path,digest in visual['images'].items():assert sha(path)==digest
 rows=gate['container_files'];assert {r['name'] for r in rows}=={NAME+'.'+ext for ext in ['pak','ucas','utoc']}
 old=read(REPO/'private/jirai-polish-v1/installation-receipt.json')['added'];assert len(old)==3
 assert snapshot()==read(REPO/'private/jirai-polish-v1/installation-receipt.json')['after']
 for row in old:assert sha(MODS/row['name'])==row['sha256']
 for row in rows:assert sha(ROOT/'container'/row['name'])==row['sha256'] and not (MODS/row['name']).exists()
 if not apply:print('HYBRID_REPLACE_PREFLIGHT_PASSED');return
 now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)));record=ROOT/('installation-'+now.strftime('%Y%m%d-%H%M%S'));record.mkdir();backup=record/'rejected-polish';backup.mkdir();before=snapshot();added=[];removed=[]
 write(record/'before.json',before)
 try:
  for row in old:
   exited();shutil.move(str(MODS/row['name']),str(backup/row['name']));removed.append(row);assert sha(backup/row['name'])==row['sha256']
  for row in rows:
   exited();shutil.copy2(ROOT/'container'/row['name'],MODS/row['name']);added.append(row);assert sha(MODS/row['name'])==row['sha256']
  retained=[r for r in before if r['name'] not in {v['name'] for v in old}];after=snapshot();assert after==sorted(retained+rows,key=lambda r:r['name'])
  receipt=dict(status='installed-hash-verified-runtime-pending',installed_at=now.isoformat(),before=before,after=after,added=rows,removed=old,backup=str(backup),source_atlas_sha256=gate['source_atlas_sha256'],native_render_sha256=gate['native_render_sha256'],retained_previous_files_exact=True,game_runtime_tested=False)
  write(ROOT/'installation-receipt.json',receipt);write(record/'installation-receipt.json',receipt)
  # A failed actual mount/readback recovers the complete prior set.
  run('verify-actual-install',[sys.executable,CODE/'verify_mount.py','installed'])
  print('HYBRID_REPLACED_AND_INSTALLED_READBACK_VERIFIED',flush=True)
 except BaseException:
  for row in added:
   assert sha(MODS/row['name'])==row['sha256'];shutil.move(str(MODS/row['name']),str(record/row['name']))
  for row in removed:shutil.copy2(backup/row['name'],MODS/row['name'])
  assert snapshot()==before;write(ROOT/'installation-failure.json',dict(recovered=True,files=snapshot()));raise

if __name__=='__main__':main('--apply' in sys.argv,'--rollback' in sys.argv)
