const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('scripts/native-notifications.js','utf8');
function setup({permission='granted',reason=null,status='delivered'}={}){
  const calls=[],listeners={},alerts=[];
  const push={
    async addListener(name,fn){listeners[name]=fn;return{async remove(){delete listeners[name]}}},
    async checkPermissions(){return{receive:permission}},
    async requestPermissions(){calls.push('permission');return{receive:'granted'}},
    async register(){listeners.registration({value:'a'.repeat(64)})},
    async unregister(){calls.push('unregister')}
  };
  const ctx={window:{Capacitor:{isNativePlatform:()=>true,Plugins:{PushNotifications:push}}},user:{id:'signed-in'},console,
    async rpc(name,args){calls.push({name,args});if(name==='nudge_scrobble_game')return reason?{ok:false,reason}:{ok:true,event_id:'event'}},
    client:{from:()=>({select:()=>({eq:()=>({single:async()=>({data:{status},error:null})})})})},
    setTimeout:(fn,ms)=>{if(ms<15000)queueMicrotask(fn);return 1},clearTimeout(){},
    openCloudGame:async id=>calls.push({open:id}),quietRefreshGames:async()=>{},alert:msg=>alerts.push(msg)};
  vm.createContext(ctx);vm.runInContext(source,ctx);
  return{ctx,calls,alerts,listeners,run:code=>vm.runInContext(code,ctx)};
}
(async()=>{
  const s=setup({permission:'prompt'});
  await s.ctx.registerNativeTurnNotifications(true);
  assert(s.calls.includes('permission'));
  assert(s.calls.some(x=>x.name==='save_scrobble_native_push_token'));
  s.listeners.pushNotificationActionPerformed({notification:{data:{game_id:'00000000-0000-0000-0000-000000000001'}}});
  await Promise.resolve();assert(s.calls.some(x=>x.open));
  await s.ctx.stopNativeTurnNotifications();
  assert(s.calls.some(x=>x.name==='delete_scrobble_native_push_token'));assert(s.calls.includes('unregister'));
  const denied=setup({permission:'denied'});assert.equal(await denied.ctx.registerNativeTurnNotifications(true),null);
  assert(!denied.calls.some(x=>x.name==='save_scrobble_native_push_token'));
  for(const [reason,status,text] of [[null,'delivered','NUDGED ✓'],[null,'queued','NUDGE QUEUED'],['cooldown','delivered','NUDGE'],['notifications_off','delivered','NUDGE'],[null,'failed','NUDGE']]){
    const n=setup({reason,status}),button={disabled:false,textContent:'NUDGE'};
    await n.ctx.nudgeGame('game',button);assert.equal(button.textContent,text);
    if(reason||status==='failed'){assert(n.alerts.length);assert.equal(button.disabled,false)}
  }
  console.log('PASS: native permission and token registration, notification game opening, logout removal, denied permission, delivery confirmation, queue fallback, cooldown, and failure handling.');
})().catch(e=>{console.error(e);process.exitCode=1});
