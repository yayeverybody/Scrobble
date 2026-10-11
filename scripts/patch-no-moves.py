from pathlib import Path
p=Path('www/game-engine-v3140.js')
s=p.read_text()
def replace_once(a,b):
 global s
 if s.count(a)!=1: raise SystemExit('Endgame source mismatch: '+a[:75])
 s=s.replace(a,b,1)
replace_once('function finishComputerGame(finisher){',"""let consecutiveCpuPasses=0;
function finishComputerPassStalemate(){
  if(!cpuMode||bag.length||consecutiveCpuPasses<2)return false;
  cpuThinking=false;swapMode=false;swapSelected.clear();spectatorMode=true;
  const deductions=racks.map(rack=>rackValue(rack));
  scores=scores.map((score,i)=>score-deductions[i]);
  status.textContent='Game over — consecutive passes with an empty tile bag.';
  render();
  const n1=($('#name1')?.textContent)||'Player 1',n2=($('#name2')?.textContent)||'Computer';
  const winner=scores[0]===scores[1]?null:(scores[0]>scores[1]?0:1);
  gameOverTitle.textContent=winner===null?'It’s a tie!':`Congratulations, ${winner===0?n1:n2}!`;
  gameOverScores.innerHTML=`<div class="gameOverScoreRow"><span>${n1}</span><strong>${scores[0]}</strong></div><div class="gameOverScoreRow"><span>${n2}</span><strong>${scores[1]}</strong></div>`;
  gameOverDeduction.textContent=`Remaining tile deductions: ${n1} −${deductions[0]}; ${n2} −${deductions[1]}.`;
  gameOverOverlay.classList.remove('hidden');
  window.dispatchEvent(new CustomEvent('scrobble:game-over',{detail:{reason:'two_passes_empty_bag',scores:[...scores],difficulty:cpuDifficulty}}));
  return true
}
function finishComputerGame(finisher){""")
replace_once('function commit(words,points){\n  scores[current]+=points;', 'function commit(words,points){\n  consecutiveCpuPasses=0;\n  scores[current]+=points;')
replace_once('  if(bag.length>=2&&racks[1].length){', '  if(bag.length>=2&&racks[1].length){\n    consecutiveCpuPasses=0;')
replace_once('  }else{\n    current=0;cpuThinking=false;refreshQuadSpaces(true);lastMoveSummary=', '  }else{\n    consecutiveCpuPasses++;\n    if(finishComputerPassStalemate())return;\n    current=0;cpuThinking=false;refreshQuadSpaces(true);lastMoveSummary=')
replace_once('draw(current);bag.push(...old);shuffle(bag);swapMode=false;', 'draw(current);bag.push(...old);shuffle(bag);consecutiveCpuPasses=0;swapMode=false;')
replace_once("recall();const playedBy=current,playerName=", "recall();if(cpuMode){consecutiveCpuPasses++;if(finishComputerPassStalemate())return;}const playedBy=current,playerName=")
replace_once('function freshLocalGame(){hideTurnNotice();hideGameOver();startingPlayer=0;', 'function freshLocalGame(){hideTurnNotice();hideGameOver();consecutiveCpuPasses=0;spectatorMode=false;startingPlayer=0;')
replace_once('board,racks,scores,bag,current,committed,startingPlayer,weirdRules,quadSpaces,quadTurnKey,', 'board,racks,scores,bag,current,committed,startingPlayer,consecutiveCpuPasses,weirdRules,quadSpaces,quadTurnKey,')
replace_once('committed=s.committed||0;startingPlayer=', 'committed=s.committed||0;consecutiveCpuPasses=s.consecutiveCpuPasses||0;startingPlayer=')
replace_once('committed,startingPlayer,lastMoveSummary,weirdRules,quadSpaces,quadTurnKey,updatedAt:', 'committed,startingPlayer,lastMoveSummary,consecutiveCpuPasses,weirdRules,quadSpaces,quadTurnKey,updatedAt:')
replace_once('lastMoveSummary=s.lastMoveSummary||null;refreshQuadSpaces();viewRackIndex=0;', 'lastMoveSummary=s.lastMoveSummary||null;consecutiveCpuPasses=s.consecutiveCpuPasses||0;refreshQuadSpaces();viewRackIndex=0;')
p.write_text(s)
print('CPU two-pass empty-bag endgame installed')
