"""Install the verified skirt overlay without replacing another chat's files."""
from common import *
from datetime import datetime,timezone,timedelta
import argparse,shutil
def install():
 assert not game_pids(),'PBZ is running; install after it exits'
 assert snapshot()==read(W/'composition-baseline.json'),'Installed files changed; compose against the latest face again'
 report=read(W/'final-verification.json');assert report['passed']
 gates=read(W/'delivery-gates.json');assert gates['passed'] and gates['container_files']==report['container_files']
 for p,h in gates['evidence_hashes'].items():assert sha(p)==h,('Evidence changed',p)
 before=snapshot();rows=report['container_files'];assert len(rows)==3
 for r in rows:assert sha(W/'container'/r['name'])==r['sha256'] and not (MODS/r['name']).exists()
 now=datetime.now(timezone(timedelta(hours=8)));record=W/('installation-'+now.strftime('%Y%m%d-%H%M%S'));record.mkdir()
 write(record/'before.json',before);copied=[]
 try:
  for row in rows:
   assert not game_pids(),'Game started during installation'
   target=MODS/row['name']
   with target.open('xb') as f:f.write((W/'container'/row['name']).read_bytes())
   copied.append(row);assert sha(target)==row['sha256']
  after=snapshot();assert {r['name']:r['sha256'] for r in after}=={r['name']:r['sha256'] for r in before+rows}
  receipt=dict(status='installed-hash-verified-runtime-pending',installed_at=now.isoformat(),record=str(record),added=rows,before=before,after=after,retained_other_chat_face=True,game_runtime_tested=False)
  write(W/'installation-receipt.json',receipt);write(record/'receipt.json',receipt)
 except Exception:
  for row in reversed(copied):
   p=MODS/row['name'];assert sha(p)==row['sha256'];shutil.move(str(p),str(record/p.name))
  raise
 print('JK_SKIRT_INSTALLED_WITH_LATEST_FACE',flush=True)
def rollback():
 assert not game_pids();r=read(W/'installation-receipt.json');dest=Path(r['record'])/'rollback';dest.mkdir()
 for row in r['added']:
  p=MODS/row['name'];assert p.resolve().parent==MODS.resolve() and sha(p)==row['sha256'];shutil.move(str(p),str(dest/p.name))
 write(dest/'receipt.json',dict(removed=[r['name'] for r in r['added']],after=snapshot(),other_files_retained=True))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--rollback',action='store_true');a=parser.parse_args();assert a.apply,'Use --apply for an intentional installation/rollback';rollback() if a.rollback else install()
