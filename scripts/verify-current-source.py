"""Run current web build checks without installing Capacitor or requiring Xcode."""
from pathlib import Path
import subprocess,sys,tempfile
repo=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='scrobble-current-') as tmp:
    subprocess.run([sys.executable,str(repo/'scripts/prepare-board-tests.py'),tmp],check=True)
    web=str(Path(tmp)/'scrobble-mobile/www')
    checks=[['test-weird-modes.cjs',web],['verify-quad-placement.cjs',web],['verify-ssa-names.cjs',web+'/game-engine-v3140.js'],['verify-integration.cjs',web],['verify-notifications.cjs'],['verify-regressions.cjs',web],['verify-audio-fallback.cjs',web+'/scrobble-haptics.js'],['verify-friend-invite.cjs',web],['verify-haptics.cjs',web+'/scrobble-haptics.js'],['verify-splash-feedback.cjs',web+'/scrobble-haptics.js',web+'/styles-v2930.css'],['verify-score-feedback.cjs',web+'/game-engine-v3140.js'],['verify-rack-drop.cjs',web+'/game-engine-v3140.js'],['verify-push-worker.cjs']]
    failed=[]
    for name,*args in checks:
        result=subprocess.run(['node',str(repo/'scripts'/name),*args],cwd=repo)
        if result.returncode:failed.append(name)
    for name in ['app-v3140.js','game-engine-v3140.js','scrobble-haptics.js']:
        if subprocess.run(['node','--check',web+'/'+name],cwd=repo).returncode:failed.append(name)
    if failed:raise SystemExit('Failed checks: '+', '.join(failed))
print('PASS: all current-source web checks. Native build and two-iPhone release gate still required.')
