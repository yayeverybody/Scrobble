"""Add direct player lookup and in-app invitation inbox to the existing Scrobble UI.
Runs after patch-ios.py; preserves shareable invitation links.
"""
from pathlib import Path
p=Path('www/app-v3140.js')
s=p.read_text()
anchor="  function askEndGame(id){"
if s.count(anchor)!=1:raise SystemExit('Direct invite app anchor missing')
js=r"""
  // Direct invites use the existing server-created game and secure invitation RPCs.
  const directPanel=document.createElement('section');
  directPanel.id='scrobbleDirectInvite';
  directPanel.innerHTML='<div style="margin:12px 0;color:#fff;font-weight:800">INVITE A SCROBBLE PLAYER</div><input id="directPlayerSearch" maxlength="40" placeholder="Search by username (2+ letters)" autocomplete="off" style="width:100%;box-sizing:border-box;padding:12px;border-radius:9px"><div id="directPlayerResults" role="status" style="margin:8px 0"></div><p style="color:#eee;font-size:13px">Or use Create Game to share a link with someone new.</p>';
  friendModePanel.insertBefore(directPanel,startFriendGame);
  const directSearch=directPanel.querySelector('#directPlayerSearch');
  const directResults=directPanel.querySelector('#directPlayerResults');
  let directSearchSerial=0,directSending=false;
  function directMessage(message){directResults.textContent=message}
  directSearch.addEventListener('input',async()=>{
    const q=directSearch.value.trim(),serial=++directSearchSerial;
    directResults.replaceChildren();
    if(q.length<2)return;
    directMessage('Searching…');
    try{
      const players=await rpc('search_scrobble_players',{p_query:q});
      if(serial!==directSearchSerial)return;
      directResults.replaceChildren();
      if(!players?.length){directMessage('No matching players. You can still share a link.');return}
      for(const player of players){
        const b=document.createElement('button');b.type='button';
        b.textContent='INVITE '+player.display_name;
        b.style.cssText='display:block;width:100%;margin:7px 0;padding:12px;background:#f2bd45;color:#173044;border:0;border-radius:9px;font-weight:800';
        b.onclick=async()=>{
          if(directSending)return;
          directSending=true;b.disabled=true;
          try{
            await createGame();
            if(!pendingNewGame)throw Error('Could not prepare game');
            const created=await persistPendingNewGame();
            if(!created?.id)throw Error('Game could not be created');
            await rpc('send_scrobble_direct_invite',{p_game_id:created.id,p_recipient_id:player.id});
            resetFriendInvite();gameModeBox.classList.add('hidden');
            await refreshGames();
            alert('Invitation sent to '+player.display_name+'. They can accept in Scrobble.');
          }catch(e){alert('Could not invite player: '+e.message)}
          finally{directSending=false;b.disabled=false}
        };
        directResults.appendChild(b);
      }
    }catch(e){if(serial===directSearchSerial)directMessage('Player search unavailable: '+e.message)}
  });
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
p.write_text(s)
print('Direct player search, secure invite send, and accept/decline inbox installed')
