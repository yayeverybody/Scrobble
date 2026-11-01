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
 w.eval(read('game-engine-v3140.js').replace('if(!loadLocalState())freshLocalGame();',`window.__mines={randomLandMines,commit,localMineHits,setup(ps,pts=100){board=Array.from({length:15},()=>Array(15).fill(null));pending=ps.map(([r,c])=>({r,c,letter:'A'}));pending.forEach(p=>board[p.r][p.c]={letter:'A',pending:true,owner:0});racks=[['T'],['T']];bag=['E'];scores=[pts,0];current=0;committed=0;landMines=[[7,7],[7,12],[12,7],[1,1],[1,6]];},cloud(v){cloudRackMode=v},cpu(){current=1},thinking:()=>cpuThinking,red(r,c){return board[r][c]?.landMine}};if(!loadLocalState())freshLocalGame();`));
 const g=w.ScrobbleGame,t=w.__mines;
 for(let n=0;n<300;n++){
  const mines=t.randomLandMines();assert.equal(mines.length,10);
  for(let i=0;i<10;i++)for(let j=i+1;j<10;j++)assert((mines[i][0]-mines[j][0])**2+(mines[i][1]-mines[j][1])**2>=25);
 }
 g.newComputerGame('easy',['hidden_land_mines']);const initial=g.exportState();assert.equal(initial.landMines.length,10);assert.equal(w.document.querySelectorAll('.detonatedMine').length,0);
 g.loadComputerState(initial);assert.deepEqual(JSON.parse(JSON.stringify(g.exportState().landMines)),JSON.parse(JSON.stringify(initial.landMines)));
 t.setup([[7,7]]);t.commit([{word:'A',cells:[[7,7]]}],30);let state=g.exportState();assert.equal(state.scores[0],70);assert.equal(state.board[7][7].letter,'A');assert.equal(state.board[7][7].landMine,true);assert.equal(state.lastMoveSummary.points,-30);assert.equal(booms,1);assert.equal(w.document.querySelector('.landMineNoticeIcon').textContent,'💥');assert(w.document.querySelector('[data-r="7"][data-c="7"]').classList.contains('detonatedMine'));assert(w.document.getElementById('turnNoticePoints').textContent.includes('30 points deducted'));
 // The CPU cannot begin thinking behind an undismissed mine notice.
 const waitingCpu=g.runComputerTurn('easy');await waitingCpu;assert.equal(t.thinking(),false);
 // No timer or computer move may clear the player's explosion notice.
 let dismissed=false;g.waitForMineNotice().then(()=>dismissed=true);await new Promise(r=>w.setTimeout(r,20));assert.equal(dismissed,false);assert(g.isMineNoticeOpen());
 w.document.getElementById('turnNoticeOverlay').click();await Promise.resolve();assert(dismissed);assert.equal(g.isMineNoticeOpen(),false);
 // Reloading the same cloud game retains the visible notice; navigation clears it.
 const cloudState={id:'cloud-one',weird_rules:['hidden_land_mines'],board:state.board,rack:['A'],scores:[70,0],current_slot:1,bag:['E'],lastMoveSummary:state.lastMoveSummary};
 g.loadCloudState(cloudState,1);g.showTurnNotice(state.lastMoveSummary);const boomCount=booms;g.loadCloudState({...cloudState,updated_at:'later'},1);assert(g.isMineNoticeOpen());assert.equal(booms,boomCount,'Refresh never repeats the blast');
 g.showTurnNotice({...state.lastMoveSummary,points:20,landMines:[]});assert(g.isMineNoticeOpen(),'Next move cannot replace an undismissed explosion');
 w.document.getElementById('turnNoticeOk').click();assert.equal(g.isMineNoticeOpen(),false);g.loadCloudState({...cloudState,id:'different-game'},1);assert.equal(g.isMineNoticeOpen(),false);
 g.newComputerGame('easy',['hidden_land_mines']);t.setup([[7,7],[7,12]],10);t.commit([{word:'AA',cells:[[7,7],[7,12]]}],30);state=g.exportState();assert.equal(state.scores[0],-20);assert.equal(state.lastMoveSummary.landMines.length,2);
 g.newComputerGame('easy',['hidden_land_mines']);t.setup([[8,8]]);t.commit([{word:'A',cells:[[8,8]]}],30);assert.equal(g.exportState().scores[0],130);
 g.newComputerGame('easy',[]);t.setup([[7,7]]);t.commit([{word:'A',cells:[[7,7]]}],30);assert.equal(g.exportState().scores[0],130);
 g.newComputerGame('easy',['hidden_land_mines']);t.setup([[7,7]]);t.cpu();t.commit([{word:'A',cells:[[7,7]]}],30);assert.equal(g.exportState().scores[1],-30,'Computer has the same mine penalty');
 g.newComputerGame('easy',['hidden_land_mines']);t.setup([[7,7]]);t.cloud(true);assert.equal(t.localMineHits().length,0,'Cloud positions are resolved exclusively on server');
 console.log('PASS: 300 random boards, ten separated mines, hidden state, save/reload, negative scores, one deduction for multiple mines, classic unaffected, server-only cloud resolution, red tile and explosion notice');
}finally{dom?.window.close();fs.rmSync(dir,{recursive:true,force:true})}})().catch(e=>{console.error(e);process.exitCode=1});
