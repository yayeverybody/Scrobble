"""Patch the ACTUAL legacy Capacitor archive. Fail if any expected source differs."""
from pathlib import Path
root=Path("scrobble-mobile/www")
html_path=root/"index.html"
app_path=root/"app-v3140.js"
engine_path=root/"game-engine-v3140.js"
html=html_path.read_text()
app=app_path.read_text()
engine=engine_path.read_text()
def replace_once(source,old,new,description):
    if source.count(old)!=1:
        raise SystemExit(f"Unexpected source for {description}: {source.count(old)} matches")
    return source.replace(old,new,1)
start=html.index('      <div class="weirdSub">Optional. Choose one.</div>')
end=html.index('    </div>',start)
html=html[:start]+'''      <div class="weirdSub">Optional. Mix and match.</div>
      <label class="weirdChoice"><input type="checkbox" value="quad_chaos"><span><strong>Crazy Random Bonus Spots</strong><small>Five floating 4× word bonuses move after every turn.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="name_dropper"><span><strong>Name Dropper</strong><small>Names, places and other proper nouns are allowed.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="suffix_suffocation"><span><strong>Suffixly</strong><small>Extra S, D, R and Y tiles in the bag.</small></span></label>
'''+html[end:]
app=replace_once(app,"  const WEIRD_LABELS={","  const WEIRD_LABELS={\n    quad_chaos:'Crazy Random Bonus Spots',\n    name_dropper:'Name Dropper',\n    suffix_suffocation:'Suffixly',","new mode labels")
app=replace_once(app,"  gameModeBox.querySelectorAll('.weirdChoice input').forEach(input=>input.addEventListener('change',()=>{if(input.checked)gameModeBox.querySelectorAll('.weirdChoice input').forEach(other=>{if(other!==input)other.checked=false})}));","  // Multiple Make It Weird rules can be selected together.","multi-select")
engine=replace_once(engine,"  const a=[];\n  Object.entries(counts).forEach(([l,n])=>{for(let i=0;i<n;i++)a.push(l)});\n  shuffle(a);\n  return a","  if(hasWeirdRule('suffix_suffocation')){for(const [letter,n] of Object.entries({S:4,D:3,R:3,Y:2}))counts[letter]=(counts[letter]||0)+n}\n  const a=[];\n  Object.entries(counts).forEach(([l,n])=>{for(let i=0;i<n;i++)a.push(l)});\n  shuffle(a);\n  return a","suffix tile bag")
html_path.write_text(html)
app_path.write_text(app)
engine_path.write_text(engine)
print("Patched legacy archive setup, multi-select, suffix bag. Floating bonuses and proper noun acceptance still require engine implementation.")

raise SystemExit("Development build intentionally blocked: floating 4x bonuses, proper-noun approval, and no-viable-moves logic are not implemented yet.")
