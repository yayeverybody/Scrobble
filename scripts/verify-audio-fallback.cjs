const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
 for(const mode of ['missing','reject','error','success','muted']){
  const sounds=[],listeners={};const custom=mode==='missing'?null:{play:()=>mode==='reject'?Promise.reject(Error('interrupted')):Promise.resolve({audioPlayed:mode==='success',audioError:mode==='error'?'asset unavailable':undefined}),cancel:async()=>{}};
  const ctx={console,Audio:class{constructor(src){this.src=src;sounds.push(this)}play(){this.paused=false;return Promise.resolve()}pause(){this.paused=true}},localStorage:{getItem:key=>mode==='muted'&&key.endsWith('sound')?'off':null},document:{hidden:false,getElementById:()=>null,addEventListener:(type,fn)=>listeners[type]=fn},window:{addEventListener(){},Capacitor:{isNativePlatform:()=>true,Plugins:{ScrobbleFeedback:custom,Haptics:{impact:async()=>{}}}}}};
  vm.createContext(ctx);vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
  ctx.window.ScrobbleHaptics.scoreStart(0,20);ctx.window.ScrobbleHaptics.scoreProgress(0,.5,100);
  for(let i=0;i<5;i++)await Promise.resolve();
  assert.equal(sounds.length,['success','muted'].includes(mode)?0:1,mode);
  if(sounds.length){assert.equal(sounds[0].src,'feedback/note-5.wav');assert(Math.abs(sounds[0].volume-.21)<.001);ctx.document.hidden=true;listeners.visibilitychange();assert(sounds[0].paused)}
 }
 console.log('PASS: sound fallback on missing/rejected/failed native audio, no duplicate successful sound, mute preference, retained volume reduction and background cancellation.');
})();
