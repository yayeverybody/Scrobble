"""Offline Name Dropper names.

The SSA website blocks automated CI downloads with HTTP 403. We intentionally
use the checked-in curated name list instead of depending on a live service.
To add a versioned SSA snapshot later, commit the data to this repository.
"""
from pathlib import Path
p=Path('www/game-engine-v3140.js')
s=p.read_text(encoding='utf-8')
if "const properNouns=new Set((" not in s:
    raise SystemExit('Curated Name Dropper patch must run first')
if "hasWeirdRule('name_dropper')&&properNouns.has(word.toUpperCase())" not in s:
    raise SystemExit('Name Dropper validation gate missing')
if 'SARA SARAH' not in s:
    raise SystemExit('Common first names missing')
print('PASS: offline curated Name Dropper list available; no SSA network download')
