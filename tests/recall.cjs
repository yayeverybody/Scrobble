const {JSDOM}=require('jsdom');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'scrobble-recall-'));
let dom;
try {
  execFileSync('python3',[path.resolve(__dirname,'../scripts/prepare-board-tests.py'),dir]);
  const read=name=>fs.readFileSync(path.join(dir,'scrobble-mobile/www',name),'utf8');
  dom=new JSDOM(read('index.html'),{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
  const w=dom.window;
  w.fetch=async()=>({ok:true,text:async()=>read('scrobble-classic-lexicon.txt')});
  w.Element.prototype.scrollIntoView=function(){};
  w.eval(read('game-engine-v3140.js'));
  const g=w.ScrobbleGame,button=w.document.getElementById('shuffle');
  g.newComputerGame('easy',[]);
  const state=g.exportState();
  state.board[7][7]={letter:'Z',owner:1};
  state.committed=1;
  state.racks[0]=['A','A','B','C','D','E','F'];
  g.loadComputerState(state,'easy');
  const letters=()=>Array.from(g.exportState().racks[0]).sort().join('');
  assert.equal(button.querySelector('span').textContent,'SHUFFLE');
  const shuffleIcon=button.querySelector('svg path').getAttribute('d');
  assert(shuffleIcon);
  for(const column of [8,9]){
    w.document.querySelector('#rack button').click();
    w.document.querySelector('#board [data-r="7"][data-c="'+column+'"]').click();
  }
  assert.equal(button.querySelector('span').textContent,'RECALL');
  assert.notEqual(button.querySelector('svg path').getAttribute('d'),shuffleIcon,'Recall has its own icon');
  assert.equal(button.querySelectorAll('svg').length,1);
  assert.equal(g.exportState().racks[0].length,5);
  button.click();
  const recalled=g.exportState();
  assert.equal(letters(),'AABCDEF');
  assert.equal(recalled.board[7][7].letter,'Z','Keep previously played tiles');
  assert.equal(recalled.board[7][8],null);
  assert.equal(recalled.board[7][9],null);
  assert.equal(recalled.current,0,'Recall must not end the turn');
  assert.equal(button.querySelector('span').textContent,'SHUFFLE');
  assert.equal(button.querySelector('svg path').getAttribute('d'),shuffleIcon,'Shuffle icon is restored');
  button.click();
  assert.equal(letters(),'AABCDEF','Shuffle preserves every tile');
  g.setSpectator(true);
  assert(button.disabled,'Opponent turns disable the button');
  console.log('PASS: live rack/board clicks, duplicate letters, recall, committed tiles, unchanged turn, shuffle and opponent lock.');
} finally {
  if(dom)dom.window.close();
  fs.rmSync(dir,{recursive:true,force:true});
}
