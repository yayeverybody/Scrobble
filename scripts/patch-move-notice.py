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
