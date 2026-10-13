"""Add in-app invitation inbox to the existing Scrobble UI.
Runs after patch-ios.py; preserves shareable invitation links.
"""
from pathlib import Path
p=Path('www/app-v3140.js')
s=p.read_text()
anchor="  function askEndGame(id){"
if s.count(anchor)!=1:raise SystemExit('Direct invite app anchor missing')
js=r"""
  // No username search: invitations are handled by existing link flow.\n  const inbox=document.createElement('section');
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
