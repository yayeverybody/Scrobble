function seededQuadSquares(){
  const key=quadDeterministicKey();let seed=2166136261;
  for(const ch of key)seed=Math.imul(seed^ch.charCodeAt(0),16777619)>>>0;
  const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
  const occupied=[];
  for(let r=0;r<15;r++)for(let c=0;c<15;c++)if(board[r][c]&&!board[r][c].pending)occupied.push([r,c]);
  const anchors=occupied.length?occupied:[[7,7]],candidates=[];
  for(let r=0;r<15;r++)for(let c=0;c<15;c++){
    if(board[r][c]&&!board[r][c].pending)continue;
    const distance=Math.min(...anchors.map(([ar,ac])=>Math.max(Math.abs(r-ar),Math.abs(c-ac))));
    candidates.push({r,c,distance})
  }
  let best=[];
  for(let attempt=0;attempt<80;attempt++){
    const pool=attempt<60?candidates.filter(cell=>cell.distance<=3):candidates;
    const ordered=pool.map(cell=>({...cell,rank:random()}));
    ordered.sort((a,b)=>(a.distance<=3?0:a.distance)-(b.distance<=3?0:b.distance)||a.rank-b.rank);
    const picked=[];
    for(const cell of ordered){
      if(picked.every(p=>Math.max(Math.abs(p.r-cell.r),Math.abs(p.c-cell.c))>=3))picked.push(cell);
      if(picked.length===5)break;
    }
    if(picked.length>best.length)best=picked;
    if(best.length===5)break;
  }
  return best.map(({r,c})=>r+'-'+c);
}
