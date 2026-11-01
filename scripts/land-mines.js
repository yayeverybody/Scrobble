// Only local games hold concealed coordinates. Cloud games resolve traps on the server.
let landMines=[];
const mineFeedbackSeen=new WeakSet();
function randomLandMines(){
  for(let attempt=0;attempt<100;attempt++){
    const cells=Array.from({length:225},(_,i)=>[Math.floor(i/15),i%15]);shuffle(cells);
    const chosen=[];
    for(const cell of cells){
      // Chebyshev spacing covers horizontal, vertical and diagonal separation.
      if(chosen.every(([r,c])=>Math.max(Math.abs(r-cell[0]),Math.abs(c-cell[1]))>=5))chosen.push(cell);
      if(chosen.length===5)return chosen;
    }
  }
  throw new Error('Could not place five separated land mines');
}
function localMineHits(){
  if(cloudRackMode||!hasWeirdRule('hidden_land_mines'))return [];
  return pending.filter(p=>landMines.some(([r,c])=>r===p.r&&c===p.c)&&!board[p.r][p.c].landMine).map(p=>[p.r,p.c]);
}
function revealMineFeedback(summary){
  if(!summary?.landMines?.length||mineFeedbackSeen.has(summary))return;
  mineFeedbackSeen.add(summary);
  window.ScrobbleHaptics?.explosion?.();
}
function mineMessage(summary){
  return `BOOM! Hidden Land Mine. ${Math.abs(summary.points)} points deducted. The word stays.`;
}
