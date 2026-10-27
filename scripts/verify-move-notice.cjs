const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const app=fs.readFileSync(path.join(process.argv[2],'app-v3140.js'),'utf8');
const start=app.indexOf("  let lastOpponentNoticeKey='';"),end=app.indexOf('  function cloudStateFingerprint',start);
let pending=[],shown=[];
const ctx={currentGame:'shortfuse',document:{getElementById:()=>({querySelector:()=>({textContent:'Zorro'})})},profileLabel:(p,f)=>p?.display_name||f,window:{ScrobbleGame:{scheduleTask:fn=>pending.push(fn),showTurnNotice:s=>shown.push(s)}}};
vm.createContext(ctx);vm.runInContext(app.slice(start,end),ctx);
for(const move_type of ['pass','swap','play']){
 for(const slot of [1,2]){
  ctx.currentGame=move_type+slot;
  ctx.maybeShowOpponentLastMove({current_slot:slot-1,updated_at:move_type,lastMoveSummary:{playedBy:slot===1?1:0,move_type,words:move_type==='play'?['CAT']:[],points:3},['player'+(slot===1?2:1)+'_profile']:{display_name:'ShortFuse'}},slot);
  pending.shift()();assert.equal(shown.at(-1).playerName,'ShortFuse');
 }
}
ctx.currentGame='no-profile';ctx.maybeShowOpponentLastMove({current_slot:0,lastMoveSummary:{playedBy:1,move_type:'pass'}},1);pending.shift()();assert.equal(shown.at(-1).playerName,'Opponent','Never borrow Zorro from old DOM');
ctx.currentGame='saved-name';ctx.maybeShowOpponentLastMove({current_slot:0,lastMoveSummary:{playedBy:1,move_type:'pass',playerName:'Sara'}},1);pending.shift()();assert.equal(shown.at(-1).playerName,'Sara');
const count=shown.length;ctx.maybeShowOpponentLastMove({current_slot:0,lastMoveSummary:{playedBy:1,move_type:'pass',playerName:'Sara'}},1);assert.equal(pending.length,0,'Do not repeat a notice for unchanged move');assert.equal(shown.length,count);
console.log('PASS: Zorro DOM cannot leak into ShortFuse notices, play/pass/swap in both slots, safe missing-profile fallback and duplicate suppression');
