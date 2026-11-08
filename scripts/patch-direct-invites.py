"""Add in-app invitation inbox to the existing Scrobble UI.
Runs after patch-ios.py; preserves shareable invitation links.
"""
from pathlib import Path
p=Path('www/app-v3140.js')
s=p.read_text()
old_create="""  async function createGame(){
    if(!user)return;
    const btn=document.getElementById('newGameDash');btn.disabled=true;
    try{
      const weird=selectedWeirdRules();
      window.ScrobbleGame.newGame(weird);
      const state=window.ScrobbleGame.exportState(),invite=code();
      openInvite(invite,state);clearWeirdRules()
"""
new_create="""  function prepareFriendGame(weird){
    window.ScrobbleGame.newGame(weird);
    return {...window.ScrobbleGame.exportState(),weirdRules:[...weird],invite_code:code()};
  }
  async function createGame(weird=selectedWeirdRules()){
    if(!user||sendingDirectInvite)return;
    const btn=document.getElementById('newGameDash');btn.disabled=true;
    try{
      const state=prepareFriendGame(weird);
      openInvite(state.invite_code,state);clearWeirdRules()
"""
if s.count(old_create)!=1:raise SystemExit('Friend game creation source changed')
s=s.replace(old_create,new_create,1)
anchor="  function askEndGame(id){"
if s.count(anchor)!=1:raise SystemExit('Direct invite app anchor missing')
js=r"""
  // Recent opponents can be invited directly; new players use links.
  const recentPanel=document.createElement('section');
  recentPanel.id='scrobbleRecentOpponents';
  recentPanel.style.cssText='margin:12px 0;color:#fff';
  const recentHeading=document.createElement('div');
  recentHeading.textContent='PLAY AGAINST SOMEONE YOU KNOW';
  recentHeading.style.cssText='font-weight:900;margin:8px 0';
  const recentItems=document.createElement('div');
  let sendingDirectInvite=false;
  recentItems.style.cssText='display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;align-items:start';
  recentPanel.append(recentHeading,recentItems);
  friendModePanel.insertBefore(recentPanel,startFriendGame);
  async function refreshRecentOpponents(){
    if(!user?.id)return;
    recentItems.textContent='Loading previous opponents…';
    try{
      const opponents=await rpc('scrobble_recent_opponents');
      recentItems.replaceChildren();
      if(!opponents?.length){recentPanel.hidden=true;return}
      recentPanel.hidden=false;
      for(const opponent of opponents){
        const btn=document.createElement('button');btn.type='button';
        btn.style.cssText='display:flex;flex-direction:column;align-items:center;gap:5px;width:100%;min-width:0;padding:6px 2px;border:0;background:transparent;color:#fff;font-weight:700;text-align:center';
        const photo=document.createElement('div');
        photo.style.cssText='width:100%;aspect-ratio:1;border-radius:50%;background:#f2bd45;color:#173044;display:flex;align-items:center;justify-content:center;overflow:hidden;font-size:23px;font-weight:900';
        photo.textContent=(opponent.display_name||'?').trim().slice(0,1).toUpperCase();
        const name=document.createElement('span');
        name.textContent=opponent.display_name||'Player';
        name.style.cssText='font-size:11px;line-height:1.2;max-width:100%;overflow-wrap:anywhere';
        btn.append(photo,name);
        client.from('profiles').select('avatar_url').eq('id',opponent.id).maybeSingle().then(({data})=>{
          if(!data?.avatar_url)return;
          try{
            const url=new URL(data.avatar_url,location.href);
            if(url.protocol!=='https:')return;
            const img=document.createElement('img');
            img.src=url.href;
            img.alt='';
            img.loading='lazy';
            img.style.cssText='width:100%;height:100%;object-fit:cover';
            img.onerror=()=>{photo.textContent=(opponent.display_name||'?').trim().slice(0,1).toUpperCase()};
            photo.replaceChildren(img);
          }catch(e){}
        }).catch(()=>{});
        btn.onclick=async()=>{
          if(sendingDirectInvite)return;
          const rules=selectedWeirdRules();
          const mode=rules.length?weirdRuleList(rules).join(', '):'Regular game';
          const opponentName=opponent.display_name||'your opponent';
          if(!window.confirm('Invite '+opponentName+'?\n\n'+mode))return;
          sendingDirectInvite=btn.disabled=true;
          try{
            pendingNewGame=prepareFriendGame(rules);
            const created=await persistPendingNewGame();
            if(!created?.id)throw Error('Game could not be saved');
            await rpc('set_scrobble_weird_rules',{p_game_id:created.id,p_rules:rules});
            const savedGame=await rpc('get_scrobble_game',{p_game_id:created.id});
            const savedRules=savedGame?.weird_rules;
            if(!Array.isArray(savedRules)||savedRules.length!==rules.length||
               !rules.every(rule=>savedRules.includes(rule))){
              throw Error('The selected Weird rules were not saved. Please try again.');
            }
            await rpc('send_scrobble_direct_invite',{p_game_id:created.id,p_recipient_id:opponent.id});
            clearWeirdRules();
            resetFriendInvite();
            gameModeBox.classList.add('hidden');
            await refreshGames();
            alert('Invitation sent to '+opponentName+'.');
          }catch(e){
            pendingNewGame=null;
            alert('Could not send invitation: '+e.message);
          }
          finally{sendingDirectInvite=btn.disabled=false}
        };
        recentItems.appendChild(btn);
      }
    }catch(e){recentItems.textContent='Previous opponents unavailable. You can still share a link.'}
  }
  playFriendMode.addEventListener('click',()=>refreshRecentOpponents());
  const inbox=document.createElement('section');
  inbox.id='scrobbleDirectInbox';
  inbox.style.cssText='margin:12px 0;padding:12px;border-radius:12px;background:#133e60;color:#fff';
  const inboxTitle=document.createElement('div');inboxTitle.textContent='GAME INVITATIONS';inboxTitle.style.fontWeight='900';
  const inboxItems=document.createElement('div');
  inbox.append(inboxTitle,inboxItems);
  document.getElementById('newGameDash').parentNode.appendChild(inbox);
  inbox.hidden=true;
  async function refreshDirectInvites(){
    if(!user?.id){inbox.hidden=true;return}
    const {data,error}=await client.from('scrobble_direct_invites')
      .select('id,game_id,sender_id,created_at').eq('recipient_id',user.id).eq('status','pending')
      .order('created_at',{ascending:false}).limit(20);
    if(error)throw error;
    inboxItems.replaceChildren();inbox.hidden=!data?.length;
    if(!data?.length)return;
    const senderIds=[...new Set(data.map(x=>x.sender_id))];
    const {data:profiles}=await client.from('profiles').select('id,display_name').in('id',senderIds);
    const names=new Map((profiles||[]).map(x=>[x.id,x.display_name]));
    for(const inv of data){
      const line=document.createElement('div');line.style.cssText='padding:10px 0;border-bottom:1px solid #50728a';
      const name=document.createElement('div');name.textContent=(names.get(inv.sender_id)||'A Scrobble player')+' invited you to play';
      const yes=document.createElement('button');yes.textContent='ACCEPT';
      const no=document.createElement('button');no.textContent='DECLINE';
      for(const b of [yes,no])b.style.cssText='margin:7px 8px 0 0;padding:9px 14px;border-radius:8px;border:0;font-weight:800';
      yes.style.background='#f2bd45';no.style.background='#e1e5ea';
      async function respond(accept){
        yes.disabled=no.disabled=true;
        try{
          await rpc('respond_scrobble_direct_invite',{p_invite_id:inv.id,p_accept:accept});
          await refreshGames();
          if(accept)alert('Game accepted! Open it from your Games list.');
        }catch(e){alert('Could not respond to invitation: '+e.message);yes.disabled=no.disabled=false}
      }
      yes.onclick=()=>respond(true);no.onclick=()=>respond(false);
      line.append(name,yes,no);inboxItems.appendChild(line);
    }
  }
"""
s=s.replace(anchor,js+"\n"+anchor,1)
refresh="  async function refreshGames(prefetchedGames=null){"
if s.count(refresh)!=1:raise SystemExit('Refresh games anchor missing')
s=s.replace(refresh,refresh+"\n    refreshDirectInvites().catch(e=>console.warn('Invite inbox refresh failed',e));",1)
# A notification can arrive before the recipient has accepted the invitation.
# Route that game to the invitation inbox before requesting member-only state.
open_game="""    try{
      const s=await rpc('get_scrobble_game',{p_game_id:id});"""
pending_game="""    try{
      const {data:pendingInvite,error:inviteError}=await client.from('scrobble_direct_invites')
        .select('id').eq('game_id',id).eq('recipient_id',user.id).eq('status','pending').maybeSingle();
      if(inviteError)throw inviteError;
      if(pendingInvite){
        showDash();
        await refreshGames();
        return;
      }
      const s=await rpc('get_scrobble_game',{p_game_id:id});"""
if s.count(open_game)!=1:raise SystemExit('Open cloud game source changed')
s=s.replace(open_game,pending_game,1)
p.write_text(s)
print('Recent opponents and in-app invitation inbox installed')
