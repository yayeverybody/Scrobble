const {JSDOM}=require('jsdom');
const fs=require('fs'),os=require('os'),path=require('path'),assert=require('assert/strict'),{execFileSync}=require('child_process');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'scrobble-mines-'));
let dom;
(async()=>{try{
 const repo=path.resolve(__dirname,'..');execFileSync('python3',[path.join(repo,'scripts/prepare-board-tests.py'),dir]);
 const read=n=>fs.readFileSync(path.join(dir,'scrobble-mobile/www',n),'utf8');
 dom=new JSDOM(read('index.html'),{url:'http://localhost',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window;let booms=0;w.ScrobbleHaptics={explosion(){booms++}};
 w.fetch=async()=>({ok:true,text:async()=>read('scrobble-classic-lexicon.txt')});w.Element.prototype.scrollIntoView=function(){};
 w.eval(read('game-engine-v3140.js').replace('if(!loadLocalState())freshLocalGame();',`window.__mines={randomLandMines,commit,localMineHits,setup(ps,pts=100){board=Array.from({length:15},()=>Array(15).fill(null));pending=ps.map(([r,c])=>({r,c,letter:'A'}));pending.forEach(p=>board[p.r][p.c]={letter:'A',pending:true,owner:0});racks=[['T'],['T']];bag=['E'];scores=[pts,0];current=0;committed=0;landMines=[[7,7],[7,12],[12,7],[1,1],[1,6]];},cloud(v){cloudRackMode=v},cpu(){current=1},red(r,c){return board[r][c]?.landMine}};if(!loadLocalState())freshLocalGame();`));
 const g=w.ScrobbleGame,t=w.__mines;
 for(let n=0;n<300;n++){
  const mines=t.randomLandMines();assert.equal(mines.length,5);
  for(let i=0;i<5;i++)for(let j=i+1;j<5;j++)assert(Math.max(Math.abs(mines[i][0]-mines[j][0]),Math.abs(mines[i][1]-mines[j][1]))>=5);
 }
 g.newComputerGame('easy',['hidden_land_mines']);const initial=g.exportState();assert.equal(initial.landMines.length,5);assert.equal(w.document.querySelectorAll('.detonatedMine').length,0);
 g.loadComputerState(initial);assert.deepEqual(JSON.parse(JSON.stringify(g.exportState().landMines)),JSON.parse(JSON.stringify(initial.landMines)));
 t.setup([[7,7]]);t.commit([{word:'A',cells:[[7,7]]}],30);let state=g.exportState();assert.equal(state.scores[0],70);assert.equal(state.board[7][7].letter,'A');assert.equal(state.board[7][7].landMine,true);assert.equal(state.lastMoveSummary.points,-30);assert.equal(booms,1);assert.equal(w.document.querySelector('.landMineNoticeIcon').textContent,'💥');assert(w.document.querySelector('[data-r="7"][data-c="7"]').classList.contains('detonatedMine'));assert(w.document.getElementById('turnNoticePoints').textContent.includes('30 points deducted'));
 g.newComputerGame('easy',['hidden_land_mines']);t.setup([[7,7],[7,12]],10);t.commit([{word:'AA',cells:[[7,7],[7,12]]}],30);state=g.exportState();assert.equal(state.scores[0],-20);assert.equal(state.lastMoveSummary.landMines.length,2);
 g.newComputerGame('easy',['hidden_land_mines']);t.setup([[8,8]]);t.commit([{word:'A',cells:[[8,8]]}],30);assert.equal(g.exportState().scores[0],130);
 g.newComputerGame('easy',[]);t.setup([[7,7]]);t.commit([{word:'A',cells:[[7,7]]}],30);assert.equal(g.exportState().scores[0],130);
 g.newComputerGame('easy',['hidden_land_mines']);t.setup([[7,7]]);t.cpu();t.commit([{word:'A',cells:[[7,7]]}],30);assert.equal(g.exportState().scores[1],-30,'Computer has the same mine penalty');
 g.newComputerGame('easy',['hidden_land_mines']);t.setup([[7,7]]);t.cloud(true);assert.equal(t.localMineHits().length,0,'Cloud positions are resolved exclusively on server');
 console.log('PASS: 300 random boards, five separated mines, hidden state, save/reload, negative scores, one deduction for multiple mines, classic unaffected, server-only cloud resolution, red tile and explosion notice');
}finally{dom?.window.close();fs.rmSync(dir,{recursive:true,force:true})}})().catch(e=>{console.error(e);process.exitCode=1});
