"""Reproduce the current build's web-source steps in an isolated test directory."""
from pathlib import Path
import subprocess, sys, zipfile
repo=Path(__file__).resolve().parent.parent
root=Path(sys.argv[1]).resolve()
web=root/'scrobble-mobile'
with zipfile.ZipFile(repo/'Scrobble_Mobile_0_1_Capacitor.zip') as z:z.extractall(web)
for name in ['patch-ios.py','patch-no-moves.py','patch-opening-vowels.py','patch-direct-invites.py','patch-name-dropper-names.py','patch-ssa-names.py']:
    subprocess.run([sys.executable,str(repo/'scripts'/name)],cwd=web,check=True,stdout=subprocess.DEVNULL)
subprocess.run([sys.executable,str(repo/'scripts/patch-weird-labels.py')],cwd=root,check=True,stdout=subprocess.DEVNULL)
subprocess.run([sys.executable,str(repo/'scripts/patch-game-board.py')],cwd=web,check=True,stdout=subprocess.DEVNULL)

subprocess.run([sys.executable,str(repo/'scripts/patch-vowel-mode.py')],cwd=web,check=True,stdout=subprocess.DEVNULL)
