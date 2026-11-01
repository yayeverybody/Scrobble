"""Install Hidden Land Mines after the existing release patches."""
from pathlib import Path
scripts=Path(__file__).resolve().parent

def once(s,old,new):
    assert s.count(old)==1, 'Land mine target mismatch: '+old[:100]
    return s.replace(old,new,1)
p=Path('www/game-engine-v3140.js');s=p.read_text()
s=once(s,'function hasWeirdRule(id)',(scripts/'land-mines.js').read_text()+'\nfunction hasWeirdRule(id)')
s=once(s,'function commit(words,points){', '''function commit(words,points){
  const mineHits=localMineHits();
  if(mineHits.length){points=-Math.abs(points);mineHits.forEach(([r,c])=>board[r][c].landMine=true)}''')
s=once(s,'  moveText.textContent=lastMoveSummary.text;', '''  if(mineHits.length){lastMoveSummary.landMines=mineHits;lastMoveSummary.text=mineMessage(lastMoveSummary);revealMineFeedback(lastMoveSummary)}
  moveText.textContent=lastMoveSummary.text;''')
s=once(s,'b.dataset.r=r;b.dataset.c=c;',"b.dataset.r=r;b.dataset.c=c;if(board[r][c]?.landMine){b.classList.add('detonatedMine');b.setAttribute('aria-label','Detonated land mine');}")
s=once(s,"turnNoticeOverlay.querySelector('.reviewLabel').textContent='Last move';", "turnNoticeOverlay.querySelector('.reviewLabel').innerHTML=summary.landMines?.length?'<span class=landMineNoticeIcon role=img aria-label=Explosion>💥</span>Hidden Land Mine!':'Last move';\n  revealMineFeedback(summary);")
s=once(s,"turnNoticePoints.textContent=`${summary.points} point${summary.points===1?'':'s'}`;", "turnNoticePoints.textContent=summary.landMines?.length?mineMessage(summary):`${summary.points} point${summary.points===1?'':'s'}`;")
s=s.replace('startingPlayer,weirdRules,quadSpaces,','startingPlayer,weirdRules,landMines,quadSpaces,')
s=s.replace('weirdRules,quadSpaces,','weirdRules,landMines,quadSpaces,')
s=s.replace('weirdRules=Array.isArray(s.weirdRules)?[...s.weirdRules]:[];', 'weirdRules=Array.isArray(s.weirdRules)?[...s.weirdRules]:[];landMines=Array.isArray(s.landMines)?s.landMines:[];')
s=once(s,'  draw(0);draw(1);ensureOpeningVowels(0);ensureOpeningVowels(1);refreshQuadSpaces(true);',"  landMines=hasWeirdRule('hidden_land_mines')?randomLandMines():[];draw(0);draw(1);ensureOpeningVowels(0);ensureOpeningVowels(1);refreshQuadSpaces(true);")
s=once(s,'cloudRackMode=true;quadContext=', 'cloudRackMode=true;landMines=[];quadContext=')
s=once(s,'const names={',"const names={hidden_land_mines:'Hidden Land Mines',")
# Retain the last explosion notice when resuming a local game.
s=once(s,'opponent:\'Player 2\'',"lastMoveSummary,opponent:'Player 2'")
s=once(s,"if(!s)return false;", "if(!s)return false;lastMoveSummary=s.lastMoveSummary||null;")
s=once(s,"  if(cpuMode&&playedBy===1)","  if(mineHits.length&&playedBy===0)showTurnNotice(lastMoveSummary);\n  if(cpuMode&&playedBy===1)")
s=once(s,"bar.textContent=lm?.move_type===","bar.textContent=lm?.landMines?.length?mineMessage(lm):lm?.move_type===")
p.write_text(s)
p=Path('www/app-v3140.js');s=p.read_text()
s=once(s,'const WEIRD_LABELS={',"const WEIRD_LABELS={hidden_land_mines:'Hidden Land Mines',")
# All detonations are shown to both players, including an accepted challenge.
s=once(s,'if(myTurn&&lm.playedBy===opponentIndex){',"if((myTurn&&lm.playedBy===opponentIndex)||lm.landMines?.length){")
s=once(s,"state['player'+(opponentIndex+1)+'_profile']","state['player'+(lm.playedBy+1)+'_profile']")
s=once(s,'      if(saved?.completed){',"      if(saved?.landMines?.length){const mineState=await rpc('get_scrobble_game',{p_game_id:currentGame});window.ScrobbleGame.loadCloudState(mineState,currentSlot)}\n      if(saved?.completed){")
# A finishing move uses the game-over path rather than the normal refresh.
old="await sleep(250);await refreshCurrentCloudGame(true)\n      }"
s=once(s,old,"await sleep(250);await refreshCurrentCloudGame(true)\n      }\n      if(saved?.completed&&saved?.landMines?.length)window.ScrobbleGame.showTurnNotice({words:e.detail.words,points:saved.points,landMines:saved.landMines,playerName:accountDisplayName(user)||'You'});")
s=once(s,"p_points:e.detail.points||0})}catch(wordErr)","p_points:saved.points??e.detail.points??0})}catch(wordErr)")
p.write_text(s)
p=Path('www/index.html');s=p.read_text()
old='<label class="weirdChoice"><input type="checkbox" value="name_dropper"><span><strong>Name Dropper</strong><small>Names and places are allowed; unlisted names need opponent approval.</small></span></label>'
s=once(s,old,'<label class="weirdChoice"><input type="checkbox" value="hidden_land_mines"><span><strong>Hidden Land Mines</strong><small>Five hidden traps. Hit one and your move’s points are deducted. The word stays.</small></span></label>')
s=once(s,'</head>','''<style>
#scrobble-v4 .landMineNoticeIcon{display:block;font-size:64px;line-height:1.1;margin:0 0 10px;text-transform:none}\n#scrobble-v4 .cell.detonatedMine{background:#800d18!important;box-shadow:inset 0 0 0 3px #b52b37}
#scrobble-v4 .detonatedMine .tileGraphic rect{fill:#800d18;stroke:#bc4350}
#scrobble-v4 .detonatedMine .tileGraphic text{fill:#fff}
</style></head>''')
p.write_text(s)
print('PASS: Hidden Land Mines installed; legacy proper noun games retained')
