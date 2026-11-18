"""Default dry-run. Hash-bound additive installation with rollback receipt."""
from common import *
import datetime,shutil
def exited():
 result=subprocess.run(['pwsh','-NoLogo','-NoProfile','-NonInteractive','-Command',"@(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' }).Count"],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert result.returncode==0 and result.stdout.decode().strip()=='0','PBZ is running; exit the game before installation'
def main(apply=False,rollback=False):
 assert rollback, "Polish1 rejected by user; reinstallation blocked. Only receipt-bound rollback remains available."
 exited()
 if rollback:
  receipt=read(ROOT/'installation-receipt.json');assert snapshot()==receipt['after'],'Installed set changed since this repair'
  if not apply:print('POLISH_ROLLBACK_PREFLIGHT_PASSED');return
  dest=ROOT/('rollback-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));dest.mkdir()
  for row in receipt['added']:assert sha(MODS/row['name'])==row['sha256']
  for row in receipt['added']:shutil.move(str(MODS/row['name']),str(dest/row['name']))
  assert snapshot()==receipt['before'];write(ROOT/'rollback-receipt.json',dict(restored=True,files=snapshot()));print('POLISH_ROLLED_BACK');return
 assert_baseline();gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');mount=read(ROOT/'mount-verification.json');visual=read(ROOT/'visual-review.json')
 assert gate['passed'] and gate['package_count']==3 and gate['bounded_native_changes_exact'] and gate['skeleton_sections_cloth_physics_exact'] and gate['copied_weights_readback_exact']
 assert geometry['passed'] and geometry['final_container_readback'] and mount['passed'] and mount['directory_order_independent'] and visual['reviewed']
 assert gate['native_render_sha256']==geometry['native_render_sha256']==mount['native_render_sha256']==visual['native_render_sha256']==sha(ROOT/'final-render.npz')
 assert gate['source_atlas_sha256']==geometry['source_atlas_sha256']==mount['source_atlas_sha256']==visual['source_atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
 for path,digest in visual['images'].items():assert sha(path)==digest
 rows=gate['container_files'];assert {r['name'] for r in rows}=={NAME+'.'+ext for ext in ['pak','ucas','utoc']}
 for row in rows:assert sha(ROOT/'container'/row['name'])==row['sha256'] and not (MODS/row['name']).exists()
 if not apply:print('POLISH_INSTALL_PREFLIGHT_PASSED');return
 now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)));record=ROOT/('installation-'+now.strftime('%Y%m%d-%H%M%S'));record.mkdir();before=snapshot();added=[]
 write(record/'before.json',before)
 try:
  for row in rows:
   exited();shutil.copy2(ROOT/'container'/row['name'],MODS/row['name']);added.append(row);assert sha(MODS/row['name'])==row['sha256']
  after=snapshot();assert {r['name']:r['sha256'] for r in after}=={r['name']:r['sha256'] for r in before+rows}
  receipt=dict(status='installed-hash-verified-runtime-pending',installed_at=now.isoformat(),before=before,after=after,added=rows,source_atlas_sha256=gate['source_atlas_sha256'],native_render_sha256=gate['native_render_sha256'],previous_files_exact=True,game_runtime_tested=False)
  write(ROOT/'installation-receipt.json',receipt);write(record/'installation-receipt.json',receipt);print('POLISH_INSTALLED_HASH_VERIFIED',flush=True)
 except BaseException:
  for row in added:
   assert sha(MODS/row['name'])==row['sha256'];shutil.move(str(MODS/row['name']),str(record/row['name']))
  assert snapshot()==before
  raise
if __name__=='__main__':main('--apply' in sys.argv,'--rollback' in sys.argv)
