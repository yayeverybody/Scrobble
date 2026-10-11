from pathlib import Path
p=Path('www/game-engine-v3140.js')
s=p.read_text()
def one(old,new):
 global s
 n=s.count(old)
 if n!=1: raise SystemExit(f'No-move patch mismatch ({n}): {old[:85]}')
 s=s.replace(old,new,1)
one('function finishComputerGame(finisher){', '''let consecutiveNoPlayTurns=0;
function finishStalledComputerGame(){
  if(!cpuMode||bag.length)return false;
  cpuThinking=false;swapMode=false;swapSelected.clear();spectatorMode=true;current=0;
  status.textContent='Game over — both players passed and no tiles remain to exchange.';
  render();
  const n1=($('#name1')?.textContent)||'Player 1',n2=($('#name2')?.textContent)||'Computer';
  const winner=scores[0]===scores[1]?null:(scores[0]>scores[1]?0:1);
  gameOverTitle.textContent=winner===null?'It’s a tie!':`Congratulations, ${winner===0?n1:n2}!`;
  gameOverScores.innerHTML=`<div class="gameOverScoreRow"><span>${n1}</span><strong>${scores[0]}</strong></div><div class="gameOverScoreRow"><span>${n2}</span><strong>${scores[1]}</strong></div>`;
  gameOverDeduction.textContent='Both players passed with no tiles left to exchange. Highest score wins.';
  gameOverOverlay.classList.remove('hidden');
  window.dispatchEvent(new CustomEvent('scrobble:game-over',{detail:{reason:'consecutive_passes',scores:[...scores],difficulty:cpuDifficulty}}));
  return true
}
function finishComputerGame(finisher){''')
one('function commit(words,points){\n  scores[current]+=points;', 'function commit(words,points){\n  consecutiveNoPlayTurns=0;\n  scores[current]+=points;')
one('  if(bag.length>=2&&racks[1].length){', '  if(bag.length>=2&&racks[1].length){\n    consecutiveNoPlayTurns=0;')
one("  }else{\n    current=0;cpuThinking=false;refreshQuadSpaces(true);lastMoveSummary={playedBy:1,playerName:'Computer',move_type:'pass'", "  }else{\n    consecutiveNoPlayTurns++;\n    if(consecutiveNoPlayTurns>=2&&finishStalledComputerGame())return;\n    current=0;cpuThinking=false;refreshQuadSpaces(true);lastMoveSummary={playedBy:1,playerName:'Computer',move_type:'pass'")
one('draw(current);bag.push(...old);shuffle(bag);swapMode=false;', 'draw(current);bag.push(...old);shuffle(bag);consecutiveNoPlayTurns=0;swapMode=false;')
one("$('#pass').onclick=()=>{if(spectatorMode){status.textContent=\"You can view this board, but it’s your opponent’s turn.\";return}recall();const playedBy=current", "$('#pass').onclick=()=>{if(spectatorMode){status.textContent=\"You can view this board, but it’s your opponent’s turn.\";return}recall();consecutiveNoPlayTurns++;if(consecutiveNoPlayTurns>=2&&finishStalledComputerGame())return;const playedBy=current")
one('function freshLocalGame(){hideTurnNotice();hideGameOver();startingPlayer=0;', 'function freshLocalGame(){hideTurnNotice();hideGameOver();consecutiveNoPlayTurns=0;spectatorMode=false;startingPlayer=0;')
one('lastMoveSummary,weirdRules,quadSpaces,quadTurnKey,updatedAt:', 'lastMoveSummary,consecutiveNoPlayTurns,weirdRules,quadSpaces,quadTurnKey,updatedAt:')
one('lastMoveSummary=s.lastMoveSummary||null;refreshQuadSpaces();viewRackIndex=0;', 'lastMoveSummary=s.lastMoveSummary||null;consecutiveNoPlayTurns=s.consecutiveNoPlayTurns||0;refreshQuadSpaces();viewRackIndex=0;')
p.write_text(s)
print('Enabled local CPU deadlock finish after consecutive passes with empty bag.')
