// Enumerate spellings that fit the available two-letter tile inventory.
function* cpuTileSpellings(word, specialCounts, offset=0, tiles=[]){
  if(offset===word.length){
    yield tiles;
    return;
  }
  yield* cpuTileSpellings(word,specialCounts,offset+1,[...tiles,word[offset]]);
  const pair=word.slice(offset,offset+2);
  if(specialCounts[pair]>0){
    specialCounts[pair]--;
    yield* cpuTileSpellings(word,specialCounts,offset+2,[...tiles,pair]);
    specialCounts[pair]++;
  }
}
function cpuFindMoves(){
  const rackCounts=cpuRackCounts();
  const specialCounts=Object.fromEntries(twoLetterTiles.map(tile=>[tile,rackCounts[tile]||0]));
  const moves=[],anchors={};
  if(committed){
    for(let r=0;r<15;r++)for(let c=0;c<15;c++){
      const cell=board[r][c];
      if(!cell)continue;
      (anchors[cell.letter]||(anchors[cell.letter]=[])).push([r,c]);
      if(twoLetterTiles.includes(cell.letter))specialCounts[cell.letter]++;
    }
  }
  const extraLetters=Object.values(specialCounts).reduce((sum,count)=>sum+count,0);
  const maxTiles=committed?15:7;
  for(const word of computerWords){
    if(word.length<2||word.length>maxTiles+extraLetters)continue;
    const spellings=extraLetters?cpuTileSpellings(word,specialCounts):[[...word]];
    for(const tiles of spellings){
      if(tiles.length<2||tiles.length>maxTiles)continue;
      const seen=new Set();
      for(let k=0;k<tiles.length;k++){
        const positions=committed?anchors[tiles[k]]:[[7,7]];
        if(!positions)continue;
        for(const [rr,cc] of positions){
          for(const [dr,dc] of [[0,1],[1,0]]){
            const r=rr-dr*k,c=cc-dc*k;
            const key=[r,c,dr,dc].join(",");
            if(seen.has(key))continue;
            seen.add(key);
            const move=cpuEvaluatePlacement(tiles,r,c,dr,dc,rackCounts);
            if(move)moves.push(move);
          }
        }
      }
    }
  }
  return moves;
}
