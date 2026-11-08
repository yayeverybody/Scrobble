const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context={setTimeout};vm.createContext(context);
vm.runInContext(fs.readFileSync(require('node:path').join(__dirname,'../scripts/available-plays.js'),'utf8'),context);
const grid=()=>Array.from({length:15},()=>Array(15).fill(null));
function trie(words){
  const root={};
  for(const word of words){let node=root;for(const letter of word)node=node[letter]||(node[letter]={});node.end=true;}
  return root;
}
(async()=>{
  const words=trie(['AT','IT','AI','TT','QI']);
  let board=grid();
  assert.equal(await context.hasDictionaryPlay(board,['Q'],words,()=>true),false);
  assert.equal(await context.hasDictionaryPlay(board,['Q','I'],words,()=>true),true);
  board[7][7]={letter:'A'};board[7][8]={letter:'T'};
  const before=JSON.stringify(board);
  assert.equal(await context.hasDictionaryPlay(board,['I','T'],words,()=>true),true,'Parallel plays count');
  assert.equal(JSON.stringify(board),before,'Search never changes board');
  assert.equal(await context.hasDictionaryPlay(board,['Z'],words,()=>true),false);
  board=grid();board[14][13]={letter:'A'};
  assert.equal(await context.hasDictionaryPlay(board,['T'],words,()=>true),true,'Board edge placements count');
  const full=Array.from({length:15},()=>Array.from({length:15},()=>({letter:'A'})));
  assert.equal(await context.hasDictionaryPlay(full,['T'],words,()=>true),false);
  assert.equal(await context.hasDictionaryPlay(grid(),['Q'],words,()=>false),null,'Cancel stale searches');
  console.log('PASS: no plays, opening-center plays, parallel/cross plays, board edges, full board, no mutations and cancellation.');
})().catch(error=>{console.error(error);process.exitCode=1});
