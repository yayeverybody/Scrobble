// Only local games hold concealed coordinates. Cloud games resolve traps on the server.
let landMines=[];
const mineFeedbackSeen=new WeakSet();
function randomLandMines(){
  for(let attempt=0;attempt<1000;attempt++){
    const cells=Array.from({length:225},(_,i)=>[Math.floor(i/15),i%15]);shuffle(cells);
    const chosen=[];
    for(const cell of cells){
      // Straight-line distance of at least five board spaces, including diagonals.
      if(chosen.every(([r,c])=>(r-cell[0])**2+(c-cell[1])**2>=25))chosen.push(cell);
      if(chosen.length===10)return chosen;
    }
  }
  throw new Error('Could not place ten separated land mines');
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

let mineNoticeWaiters=[],mineNoticeQueued=null,mineCloudGameId=null,preserveMineNotice=false;
function isMineNoticeOpen(){return !!turnNoticeSummary?.landMines?.length&&!turnNoticeOverlay.classList.contains('hidden')}
function waitForMineNotice(){return new Promise(resolve=>{if(isMineNoticeOpen())mineNoticeWaiters.push(resolve);else resolve()})}
function releaseMineNoticeWaiters(){const callbacks=mineNoticeWaiters.splice(0);callbacks.forEach(resolve=>resolve())}
function sameMineNotice(a,b){return a?.playedBy===b?.playedBy&&a?.points===b?.points&&JSON.stringify(a?.words)===JSON.stringify(b?.words)&&JSON.stringify(a?.landMines)===JSON.stringify(b?.landMines)}
