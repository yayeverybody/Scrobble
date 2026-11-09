// Search dictionary placements without changing board, rack, score, or turn.
let playableWordTrie=null,playableTrieNames=null,availablePlayKey=null,availablePlayResult=null;
function buildPlayableWordTrie(){
  const namesAllowed=hasWeirdRule('name_dropper');
  if(playableWordTrie&&playableTrieNames===namesAllowed)return playableWordTrie;
  playableTrieNames=namesAllowed;
  const trie={};
  for(const raw of [...offlineLexicon,...dictionary,...(hasWeirdRule('name_dropper')?properNouns:[])]){
    const word=raw.toUpperCase();
    if(word.length<2||word.length>15)continue;
    let node=trie;
    for(const letter of word)node=node[letter]||(node[letter]={});
    node.end=true;
  }
  return trie;
}
async function hasDictionaryPlay(grid,rack,trie,isCurrent){
  const counts={};
  for(const letter of rack)counts[letter]=(counts[letter]||0)+1;
  const occupied=grid.some(row=>row.some(Boolean));
  const known=word=>{
    let node=trie;
    for(const letter of word){node=node[letter];if(!node)return false;}
    return !!node.end;
  };
  function crossValid(r,c,letter,dr,dc){
    let prefix='',suffix='';
    for(let rr=r-dc,cc=c-dr;rr>=0&&cc>=0&&rr<15&&cc<15&&grid[rr][cc];rr-=dc,cc-=dr)prefix=grid[rr][cc].letter+prefix;
    for(let rr=r+dc,cc=c+dr;rr>=0&&cc>=0&&rr<15&&cc<15&&grid[rr][cc];rr+=dc,cc+=dr)suffix+=grid[rr][cc].letter;
    return (!prefix&&!suffix)||known(prefix+letter+suffix);
  }
  function walk(r,c,dr,dc,node,length,placed,connected,center){
    const inside=r<15&&c<15;
    const cell=inside?grid[r][c]:null;
    if(length>=2&&placed&&node.end&&!cell&&(occupied?connected:center))return true;
    if(!inside)return false;
    if(cell){
      const next=node[cell.letter];
      return !!next&&walk(r+dr,c+dc,dr,dc,next,length+1,placed,true,center||(r===7&&c===7));
    }
    const touches=[[1,0],[-1,0],[0,1],[0,-1]].some(([rr,cc])=>grid[r+rr]?.[c+cc]);
    for(const letter of Object.keys(counts)){
      if(!counts[letter]||!node[letter]||!crossValid(r,c,letter,dr,dc))continue;
      counts[letter]--;
      const found=walk(r+dr,c+dc,dr,dc,node[letter],length+1,placed+1,connected||touches,center||(r===7&&c===7));
      counts[letter]++;
      if(found)return true;
    }
    return false;
  }
  for(let r=0;r<15;r++){
    if(!isCurrent())return null;
    for(let c=0;c<15;c++)for(const [dr,dc] of [[0,1],[1,0]]){
      if(grid[r-dr]?.[c-dc])continue;
      if(walk(r,c,dr,dc,trie,0,0,false,false))return true;
    }
    await new Promise(resolve=>setTimeout(resolve,0));
  }
  return false;
}
function updateAvailablePlayNotice(){
  let notice=$('#availablePlayNotice');
  if(!notice){
    notice=document.createElement('div');
    notice.id='availablePlayNotice';
    notice.setAttribute('role','status');
    notice.textContent='No moves. You must pass.';
    notice.style.cssText='padding:0;flex:1;min-width:0;white-space:nowrap;text-align:right;font-size:clamp(11px,3.4vw,14px);line-height:1.15;font-weight:bold;color:#ffd15b';
    const style=document.createElement('style');
    style.textContent='#scrobble-v4 .movebar.noAvailablePlays #status,#scrobble-v4 .movebar.noAvailablePlays #lastPlayBar{display:none!important}#scrobble-v4 #availablePlayNotice[hidden]{display:none!important}';
    document.head.appendChild(style);
    status.insertAdjacentElement('afterend',notice);
  }
  const showNotice=visible=>{
    notice.hidden=!visible;
    status.parentElement.classList.toggle('noAvailablePlays',visible);
  };
  const eligible=!spectatorMode&&!(cpuMode&&current===1)&&!pending.length&&!awaiting&&!cloudChallenge&&!swapMode&&racks[current]?.length;
  if(!eligible){availablePlayKey=null;showNotice(false);return;}
  const key=JSON.stringify([board,racks[current].slice().sort(),current,weirdRules]);
  const display=()=>showNotice(availablePlayResult===false);
  if(key===availablePlayKey){display();return;}
  availablePlayKey=key;availablePlayResult=null;showNotice(false);
  const grid=board.map(row=>row.map(cell=>cell?{letter:cell.letter}:null));
  const rack=[...racks[current]];
  const currentCheck=()=>availablePlayKey===key;
  offlineLexiconReadyPromise.then(async ready=>{
    if(!ready||!currentCheck())return;
    const result=await hasDictionaryPlay(grid,rack,buildPlayableWordTrie(),currentCheck);
    if(!currentCheck()||result===null)return;
    availablePlayResult=result;display();
  }).catch(()=>{if(currentCheck()){availablePlayKey=null;showNotice(false);}});
}
