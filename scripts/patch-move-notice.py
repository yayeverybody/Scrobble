"""Last-move names belong to the loaded game, never to previous board DOM."""
from pathlib import Path
app=Path('www/app-v3140.js');engine=Path('www/game-engine-v3140.js')
s=app.read_text()
old="""      const root=document.getElementById('scrobble-v4');
      const fallback=opponentIndex===0?root?.querySelector('#name1')?.textContent:root?.querySelector('#name2')?.textContent;
      const summary={...lm,playerName:lm.playerName||fallback||'Opponent'};"""
new="""      // Names can still show the previous game while openCloudGame awaits profiles.
      const opponentProfile=state['player'+(opponentIndex+1)+'_profile'];
      const summary={...lm,playerName:profileLabel(opponentProfile,lm.playerName||'Opponent')};"""
if new not in s:
    assert s.count(old)==1,'Expected current opponent notice builder'
    app.write_text(s.replace(old,new))
s=engine.read_text()
old="playerName:s.lastMoveSummary.playerName||s['player'+(s.lastMoveSummary.playedBy+1)+'_profile']?.display_name"
new="playerName:s['player'+(s.lastMoveSummary.playedBy+1)+'_profile']?.display_name||s.lastMoveSummary.playerName"
if new not in s:
    assert s.count(old)==1,'Expected current restored last-move summary'
    engine.write_text(s.replace(old,new))
print('PASS: last-move player names come from the loaded game, not previous DOM')

# Retain the scored word paths; spelling alone cannot identify a move.
s=engine.read_text()
old="words:words.map(w=>w.word),points,text:"
new="words:words.map(w=>w.word),wordPaths:words.map(w=>({word:w.word,cells:w.cells.map(([r,c])=>[r,c])})),points,text:"
if new not in s:
    assert s.count(old)==1,'Expected committed move summary'
    s=s.replace(old,new)
start=s.index('function animateLastMove(summary){')
end=s.index('  if(!cells.length)return;',start)
replacement='''function lastMoveCells(summary){
  const cellMap=new Map();
  // Old saved moves have no coordinates. Skip their animation rather than
  // guessing among repeated words elsewhere on the board.
  for(const path of summary?.wordPaths||[]){
    const word=String(path.word||'').toUpperCase(),cells=path.cells;
    if(!Array.isArray(cells)||cells.length!==word.length||!cells.length)continue;
    const valid=cells.every((cell,i)=>{
      if(!Array.isArray(cell)||cell.length!==2)return false;
      const [r,c]=cell;
      if(!Number.isInteger(r)||!Number.isInteger(c)||r<0||r>=15||c<0||c>=15)return false;
      if(board?.[r]?.[c]?.letter!==word[i])return false;
      if(i){const [pr,pc]=cells[i-1];if(i===1){if(!((r===pr&&c===pc+1)||(r===pr+1&&c===pc)))return false;}
        else if(r-pr!==cells[1][0]-cells[0][0]||c-pc!==cells[1][1]-cells[0][1])return false;}
      return true
    });
    if(valid)cells.forEach(([r,c])=>cellMap.set(`${r}-${c}`,[r,c]))
  }
  return [...cellMap.values()]
}
function animateLastMove(summary){
  if(!summary?.words?.length)return;
  const cells=lastMoveCells(summary);
'''
s=s[:start]+replacement+s[end:]
engine.write_text(s)
print('PASS: last-move animation uses recorded word coordinates')
