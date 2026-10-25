const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const calls=[],events={},inputs={};
 for(const key of ['sound','haptics']) inputs['feedback-'+key]={checked:true,addEventListener:(name,fn)=>inputs[key+'Change']=fn};
 const ctx={console,localStorage:{getItem:()=>null,setItem(){}},document:{hidden:false,getElementById:id=>inputs[id],addEventListener(){}},window:{addEventListener:(name,fn)=>events[name]=fn,Capacitor:{isNativePlatform:()=>true,Plugins:{ScrobbleFeedback:{play:async p=>{calls.push(p);return {audioPlayed:true}},cancel:async()=>{}},Haptics:{}}}}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync('scripts/scrobble-haptics.js','utf8'),ctx);
 const h=ctx.window.ScrobbleHaptics;
 h.tile();h.tile();h.tile();h.tileReturn();h.error();h.shuffle();h.tap();
 assert.deepEqual(calls.map(c=>c.soundName),['tile-0','tile-1','tile-2','return','error','shuffle','button']);
 assert(calls.every(c=>c.sound));
 h.scoreStart(0,60);h.scoreEnd(0);assert.equal(calls.at(-1).soundName,'big-finish');
 h.scoreStart(0,10);h.scoreEnd(0);assert.equal(calls.at(-1).soundName,'finish');
 inputs['feedback-sound'].checked=false;inputs.soundChange();h.tile();assert.equal(calls.at(-1).sound,false);assert.equal(calls.at(-1).haptics,true);
 ctx.document.hidden=true;const count=calls.length;h.tile();assert.equal(calls.length,count);
 console.log('PASS: native sample mapping, placement variations, large-score reward, independent sound mute and background suppression');
})().catch(e=>{console.error(e);process.exitCode=1});
