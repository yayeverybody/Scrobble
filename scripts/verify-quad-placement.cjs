const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const engine=fs.readFileSync((process.argv[2]||'www')+'/game-engine-v3140.js','utf8');
const from=engine.indexOf('function seededQuadSquares(){'),to=engine.indexOf('function refreshQuadSpaces(',from);
assert(from>=0&&to>from);
for(let turn=0;turn<100;turn++){
  const board=Array.from({length:15},()=>Array(15).fill(null));board[7][7]={letter:'A'};
  const ctx={board,quadDeterministicKey:()=>`game:${turn}`};vm.createContext(ctx);vm.runInContext(engine.slice(from,to),ctx);
  const first=Array.from(ctx.seededQuadSquares());assert.equal(first.length,5);assert.deepEqual(Array.from(ctx.seededQuadSquares()),first);
  const cells=first.map(key=>key.split('-').map(Number));
  for(let i=0;i<cells.length;i++){
    const [r,c]=cells[i];assert(!board[r][c]);assert(Math.max(Math.abs(r-7),Math.abs(c-7))<=3);
    for(const [rr,cc] of cells.slice(i+1))assert(Math.max(Math.abs(r-rr),Math.abs(c-cc))>=3);
  }
}
console.log('PASS: 100 seeded layouts, five unoccupied nearby spaces, minimum spacing, repeatable per-turn layout');
