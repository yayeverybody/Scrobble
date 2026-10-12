"""Extend Name Dropper with SSA's official national baby-name data at build time.

SSA national file: https://www.ssa.gov/oact/babynames/names.zip
Counts are aggregated over all available years and sexes. A name is accepted if
it appears in at least 100 recorded births, or at least 25 births since 2000.
Names must be alphabetic and 2-15 characters. Existing curated names remain.
This is a build-time import; no network request or personal data is needed in-game.
"""
from collections import Counter
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile
import re

URL='https://www.ssa.gov/oact/babynames/names.zip'
p=Path('www/game-engine-v3140.js')
s=p.read_text(encoding='utf-8')
anchor="const properNouns=new Set(("
if s.count(anchor)!=1:
    raise SystemExit('SSA names patch requires curated Name Dropper patch first')
req=Request(URL,headers={'User-Agent':'Scrobble-NameDropper/1.0 (public SSA data import)'})
try:
    with urlopen(req,timeout=35) as response:
        data=response.read(15_000_001)
except Exception as exc:
    raise SystemExit(f'Could not retrieve official SSA national names archive: {exc}')
if len(data)>15_000_000: raise SystemExit('SSA archive exceeds expected size')
totals=Counter()
recent=Counter()
with ZipFile(BytesIO(data)) as archive:
    files=[f for f in archive.namelist() if re.fullmatch(r'yob(18|19|20)\d\d\.txt',f)]
    if len(files)<120: raise SystemExit(f'Unexpected SSA archive: only {len(files)} yearly files')
    for filename in files:
        year=int(filename[3:7])
        for line in archive.read(filename).decode('utf-8-sig').splitlines():
            fields=line.split(',')
            if len(fields)!=3: continue
            name,sex,count=fields
            name=name.upper()
            if not re.fullmatch(r'[A-Z]{2,15}',name):continue
            n=int(count)
            totals[name]+=n
            if year>=2000: recent[name]+=n
names=sorted(name for name,n in totals.items() if n>=100 or recent[name]>=25)
if len(names)<4000 or not {'SARA','SARAH','JOSHUA','EMILY','MICHAEL'}.issubset(names):
    raise SystemExit(f'SSA name validation failed: {len(names)} names')
# Add after the original Set initialization, leaving the original names and
# normal dictionary/opponent-review behavior intact.
needle=").split(' '));"
i=s.index(anchor)
j=s.find(needle,i)
if j<0:raise SystemExit('SSA insertion anchor not found')
j+=len(needle)
payload="\n// SSA national baby names, imported at build time (1880 onward).\n"+ "for(const n of '"+' '.join(names)+"'.split(' '))properNouns.add(n);"
s=s[:j]+payload+s[j:]
p.write_text(s,encoding='utf-8')
print(f'PASS: SSA national data added {len(names)} eligible first names from {len(files)} birth years')
