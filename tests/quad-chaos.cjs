// Install jsdom, then run: node tests/quad-chaos.cjs
const {JSDOM}=require('jsdom');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const repo=path.resolve(__dirname,'..'),dir=fs.mkdtempSync(path.join(os.tmpdir(),'scrobble-quad-'));
(async()=>{let dom;
try{
  execFileSync('unzip',['-q',path.join(repo,'Scrobble_Mobile_0_1_Capacitor.zip'),'-d',dir]);
  execFileSync('python3',[path.join(repo,'scripts/patch-ios.py')],{cwd:dir});
  const read=name=>fs.readFileSync(path.join(dir,'www',name),'utf8');
  dom=new JSDOM(read('index.html'),{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
  const w=dom.window;
  w.fetch=async()=>({ok:true,text:async()=>read('scrobble-classic-lexicon.txt')});
  w.Element.prototype.scrollIntoView=function(){};
  const hook="window.__quadTest={scoreMove,boardBonusAt,cpuCrossInfo,setCell:(r,c,t)=>{board[r][c]=t}};";
  w.eval(read('game-engine-v3140.js').replace('if(!loadLocalState())freshLocalGame();',hook+'if(!loadLocalState())freshLocalGame();'));
  const run=async function(){
    await new Promise(r=>setTimeout(r,0));
    const g=window.ScrobbleGame,q=window.__quadTest;
    const spaces=()=>[...document.querySelectorAll('#board .qw')].map(el=>[Number(el.dataset.r),Number(el.dataset.c)]);
    const base=()=>({id:'shared-game',updated_at:'turn-1',board:Array.from({length:15},()=>Array(15).fill(null)),scores:[0,0],rack:['A','A','A'],bag:['A'],current_slot:0,weird_rules:['quad_chaos']});
    let countOK=true,spacingOK=true,nearOK=true,emptyOK=true;
    for(let n=0;n<100;n++){
      const s=base();s.updated_at='turn-'+n;s.board[7][7]={letter:'A',owner:0};g.loadCloudState(s,1);
      const cells=spaces();countOK&&=cells.length===5;
      emptyOK&&=cells.every(([r,c])=>!s.board[r][c]);
      nearOK&&=cells.every(([r,c])=>Math.max(Math.abs(r-7),Math.abs(c-7))<=3);
      spacingOK&&=cells.every((a,i)=>cells.slice(i+1).every(b=>Math.max(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1]))>=3));
    }
    const s=base();s.board[7][7]={letter:'A',owner:0};g.loadCloudState(s,1);g.setSpectator(false);
    const first=JSON.stringify(spaces());
    g.loadCloudState({...s,rack:['Z','Q']},2);const shared=JSON.stringify(spaces())===first;
    g.loadCloudState(s,1);g.setSpectator(false);
    const [r,c]=spaces().find(([r,c])=>c<14&&!s.board[r][c+1]&&Math.max(Math.abs(r-7),Math.abs(c-7))>=2);
    const neighborBonus=q.boardBonusAt(r,c+1);
    const expected=4*(1+(neighborBonus==='dl'?2:neighborBonus==='tl'?3:1))*(neighborBonus==='dw'?2:neighborBonus==='tw'?3:1);
    document.querySelector('#rack .rackbtn').click();document.querySelector(`.cell[data-r="${r}"][data-c="${c}"]`).click();
    const stable=JSON.stringify(spaces())===first;
    document.querySelector('#rack .rackbtn').click();document.querySelector(`.cell[data-r="${r}"][data-c="${c+1}"]`).click();
    const scored=q.scoreMove([{word:'AA',cells:[[r,c],[r,c+1]]}]);
    g.loadCloudState({...s,updated_at:'turn-next',current_slot:1},1);const changed=JSON.stringify(spaces())!==first;
    const reload=JSON.stringify(spaces());g.loadCloudState({...s,updated_at:'turn-next',current_slot:1},1);const reloadStable=JSON.stringify(spaces())===reload;
    const cpuCell=spaces().find(([r])=>r>0&&r<14),[cr,cc]=cpuCell;
    for(let row=0;row<15;row++)q.setCell(row,cc,null);
    q.setCell(cr-1,cc,{letter:'C',owner:0});q.setCell(cr+1,cc,{letter:'T',owner:0});
    const cpuScore=q.cpuCrossInfo(cr,cc,'A',0,1).score;
    g.newComputerGame('easy',['quad_chaos']);const local=JSON.stringify(spaces());const saved=g.exportState();g.loadComputerState(saved,'easy');const resumed=JSON.stringify(spaces())===local;
    document.getElementById('pass').click();const passChanged=JSON.stringify(spaces())!==local;
    g.newComputerGame('easy',[]);const normal=spaces().length===0;
    return {countOK,spacingOK,nearOK,emptyOK,shared,stable,scored,expected,changed,reloadStable,cpuScore,resumed,passChanged,normal};
  };
  const r=JSON.parse(JSON.stringify(await w.eval('('+run.toString()+')()')));
  for(const k of ['countOK','spacingOK','nearOK','emptyOK','shared','stable','changed','reloadStable','resumed','passChanged','normal'])assert.ok(r[k],k);
  assert.equal(r.scored,r.expected);assert.equal(r.cpuScore,24);
  console.log('PASS: 100 Quad Chaos layouts; 5 empty spaces, spacing, proximity, shared/stable turns, 4× human/CPU scoring, pass, resume, normal mode');
}finally{dom?.window.close();fs.rmSync(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
