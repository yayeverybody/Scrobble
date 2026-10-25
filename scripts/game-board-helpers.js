// Injected into the existing engine closure; current rules and scoring stay intact.
let boardViewGeneration=0,cloudRackMode=false,quadContext='local',quadTurnNumber=0;
function scheduleBoardTask(callback,delay){
  const generation=boardViewGeneration;
  return setTimeout(()=>{if(generation===boardViewGeneration)callback()},delay)
}
function clearBoardPresentation(){
  boardViewGeneration++;
  turnNoticeSummary=null;
  turnNoticeOverlay.classList.add('hidden');
  wordOverlay.classList.add('hidden');hideGameOver();noticeMode=false;
  clearTimeout(movePreviewTimer);movePreviewToken++;
  moveText.textContent='';status.textContent='';
  const bar=$('#lastPlayBar');if(bar)bar.textContent='';
  boardTransform.classList.remove('slowZoomOut');
  scoreAnimations.forEach((id,slot)=>{if(id)cancelAnimationFrame(id);window.ScrobbleHaptics?.scoreCancel?.(slot)});
  scoreAnimations=[null,null];displayedScores=[null,null];
}
function renderBoardDetails(){
  const bar=$('#lastPlayBar'),lm=lastMoveSummary;
  if(bar){
    const name=lm?.playerName||(lm?.playedBy===0?$('#name1'):$('#name2'))?.textContent||'Player';
    bar.textContent=lm?.move_type==='play'?`${name} played ${(lm.words||[]).join(' / ')} for ${Number(lm.points)||0}`:'';
  }
  const label=$('#activeWeirdRules');
  if(label){
    const names={quad_chaos:'Crazy Random Bonus Spots',name_dropper:'Name Dropper',suffix_suffocation:'Suffixly',all_or_none:'All or None',too_many_ts:'All or None',vowel_movement:'Vowel Movement',high_roller:'High Roller',too_many_tiles:'Too Many Tiles',seven_heaven:'Too Many Tiles',oops_all_ys:'Oops! All Y’s'};
    const active=[...new Set(weirdRules.map(id=>names[id]||id.replace(/_/g,' ')))];
    label.textContent=active.length?'Make it weird: '+active.join(' • '):'';
    label.hidden=!active.length;
  }
}
