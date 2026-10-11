"""Guarantee at least two A/E/I/O/U tiles in each player's initial rack.
Exchanges use the existing bag and preserve its full tile distribution.
Only runs on fresh game creation, not every rack refill.
"""
from pathlib import Path
p=Path('www/game-engine-v3140.js')
s=p.read_text(encoding='utf-8')
old="function draw(p){while(racks[p].length<rackTarget()&&bag.length)racks[p].push(bag.pop())}"
if s.count(old)!=1: raise SystemExit('Initial-rack patch: draw function mismatch')
new=old+"""
function ensureOpeningVowels(player){
  const rack=racks[player];
  const isVowel=tile=>['A','E','I','O','U'].includes(String(tile).toUpperCase());
  let vowels=rack.filter(isVowel).length;
  while(vowels<2){
    const bagIndex=bag.findIndex(isVowel);
    const rackIndex=rack.findIndex(tile=>!isVowel(tile));
    if(bagIndex<0||rackIndex<0)throw Error('Insufficient vowels for opening rack');
    const vowel=bag.splice(bagIndex,1)[0];
    const displaced=rack[rackIndex];
    rack[rackIndex]=vowel;
    bag.push(displaced);
    vowels++;
  }
  shuffle(rack);
  shuffle(bag);
}
"""
s=s.replace(old,new,1)
old2="  draw(0);draw(1);refreshQuadSpaces(true);render();applyZoom(false);saveLocalState()"
if s.count(old2)!=1: raise SystemExit('Initial-rack patch: fresh game mismatch')
s=s.replace(old2,"  draw(0);draw(1);ensureOpeningVowels(0);ensureOpeningVowels(1);refreshQuadSpaces(true);render();applyZoom(false);saveLocalState()",1)
p.write_text(s,encoding='utf-8')
print('Initial racks guaranteed >=2 A/E/I/O/U each; existing bag distribution preserved')
