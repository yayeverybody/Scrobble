  let nativeToken=null,nativeListenersPromise=null,nativeRegistrationPromise=null,pendingNativeGameId=null;
  function nativePush(){
    const cap=window.Capacitor;
    if(!cap?.isNativePlatform?.())return null;
    return cap.Plugins?.PushNotifications||cap.registerPlugin?.('PushNotifications');
  }
  async function openPendingNativeGame(){
    if(!user||!pendingNativeGameId)return;
    const id=pendingNativeGameId;pendingNativeGameId=null;
    try{await openCloudGame(id)}catch(e){console.warn('Could not open notification game',e)}
  }
  function installNativePushListeners(){
    const push=nativePush();if(!push)return Promise.resolve();
    if(!nativeListenersPromise)nativeListenersPromise=(async()=>{
      await push.addListener('pushNotificationActionPerformed',event=>{
        const id=event.notification?.data?.game_id;
        if(typeof id==='string'&&/^[a-f0-9-]{36}$/i.test(id)){pendingNativeGameId=id;void openPendingNativeGame()}
      });
      await push.addListener('pushNotificationReceived',()=>{void quietRefreshGames()});
    })().catch(e=>{nativeListenersPromise=null;throw e});
    return nativeListenersPromise;
  }
  async function registerNativeTurnNotifications(ask=false){
    const push=nativePush();if(!push||!user)return null;
    await installNativePushListeners();await openPendingNativeGame();
    let permission=await push.checkPermissions();
    if(ask&&permission.receive==='prompt')permission=await push.requestPermissions();
    if(permission.receive!=='granted')return null;
    if(nativeRegistrationPromise)return nativeRegistrationPromise;
    nativeRegistrationPromise=(async()=>{
      let registration,errorListener,timer;
      try{
        const token=await new Promise(async(resolve,reject)=>{
          timer=setTimeout(()=>reject(new Error('Notification registration timed out. Please try again.')),15000);
          try{
            registration=await push.addListener('registration',value=>resolve(value.value));
            errorListener=await push.addListener('registrationError',()=>reject(new Error('Could not register for notifications. Please try again.')));
            await push.register();
          }catch(e){reject(e)}
        });
        if(!user)throw new Error('Please sign in again.');
        await rpc('save_scrobble_native_push_token',{p_token:token});nativeToken=token;
        return token;
      }finally{
        clearTimeout(timer);
        await registration?.remove();await errorListener?.remove();
        nativeRegistrationPromise=null;
      }
    })();
    return nativeRegistrationPromise;
  }
  async function stopNativeTurnNotifications(){
    if(nativeToken&&user)await rpc('delete_scrobble_native_push_token',{p_token:nativeToken});
    nativeToken=null;
    const push=nativePush();if(push)await push.unregister();
  }
  void installNativePushListeners().catch(e=>console.warn('Notification listener setup failed',e));

  async function nudgeGame(gameId,button){
    button.disabled=true;button.textContent='NUDGING…';
    try{
      const result=await rpc('nudge_scrobble_game',{p_game_id:gameId});
      if(!result?.ok){
        const messages={not_waiting:'You can nudge only when it is your opponent’s turn.',cooldown:'You already nudged this game. Try again after 12 hours.',notifications_off:'Your opponent has not turned on notifications yet.'};
        throw new Error(messages[result?.reason]||'Could not send a nudge. Please try again.');
      }
      let status='queued';
      for(let i=0;i<8;i++){
        await new Promise(resolve=>setTimeout(resolve,1000));
        const {data,error}=await client.from('scrobble_notification_events').select('status').eq('id',result.event_id).single();
        if(error)break;
        status=data.status;if(status!=='queued')break;
      }
      if(status==='failed')throw new Error('The nudge could not be delivered. Your opponent may need to enable notifications.');
      if(status==='skipped')throw new Error('The game changed before the nudge was sent. Refresh your games.');
      button.textContent=status==='delivered'?'NUDGED ✓':'NUDGE QUEUED';
    }catch(e){alert(e.message||'Could not send a nudge.');button.textContent='NUDGE';button.disabled=false}
  }
