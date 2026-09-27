from pathlib import Path

index = Path('www/index.html')
text = index.read_text()
text = text.replace('content="width=device-width,initial-scale=1"','content="width=device-width,initial-scale=1,viewport-fit=cover"')

# App Store metadata compliance: "free" is treated as a pricing reference.
# Keep the splash message but replace the pricing language.
for old_splash in ('ALWAYS FREE', 'Always Free', 'Always free'):
    text = text.replace(old_splash, 'PLAY ALL DAY')

safe_style = '''
<style id="scrobble-ios-safe-area">
@supports (padding: env(safe-area-inset-top)) {
  body.scrobbleGameActive { background:#111 !important; }
  body.scrobbleGameActive #scrobble-v4 { margin-top:env(safe-area-inset-top) !important; }
}
</style>
'''
if 'id="scrobble-ios-safe-area"' not in text:
    text = text.replace('</head>', safe_style + '</head>')

logout_html = '<button id="logoutAccount" class="logoutAccount hidden" type="button">LOG OUT</button>'
delete_html = logout_html + '<button id="deleteAccount" class="deleteAccount hidden" type="button">DELETE ACCOUNT</button>'
if 'id="deleteAccount"' not in text:
    if logout_html not in text:
        raise SystemExit('Delete-account button insertion target not found')
    text = text.replace(logout_html, delete_html, 1)

delete_style = '''
<style id="scrobble-delete-account-style">
#accountBox .deleteAccount{width:100%;min-height:48px;margin-top:10px;border:1px solid #b42318;border-radius:12px;background:#fff;color:#b42318;font:900 14px Arial,Helvetica,sans-serif}
#accountBox .deleteAccount.hidden{display:none!important}
</style>
'''
if 'id="scrobble-delete-account-style"' not in text:
    text = text.replace('</head>', delete_style + '</head>')
index.write_text(text)

fit = Path('www/viewport-fit-v2670.js')
js = fit.read_text()
old = 'const available=Math.max(1,viewportHeight());'
new = 'const safeTop=parseFloat(getComputedStyle(root).marginTop)||0;\n      const available=Math.max(1,viewportHeight()-safeTop);'
if old in js:
    js = js.replace(old, new)
fit.write_text(js)

engine = Path('www/game-engine-v3140.js')
game = engine.read_text()
old_hit = 'const q=rackEl.getBoundingClientRect(),hit={left:q.left-8,right:q.right+8,top:q.top-18,bottom:q.bottom+18};'
new_hit = 'const q=rackEl.getBoundingClientRect(),hit={left:q.left-18,right:q.right+18,top:q.top-55,bottom:q.bottom+55};'
if old_hit in game:
    game = game.replace(old_hit, new_hit, 1)
elif new_hit not in game:
    raise SystemExit('Rack hit-zone patch target not found')

# The larger rack return zone fixed dragging pending tiles back to the rack, but it
# overlaps the board's bottom row on iPhone. Give the board first refusal near its
# edge; the rack still wins everywhere below the board snap tolerance.
old_target = "const q=rackEl.getBoundingClientRect(),hit={left:q.left-18,right:q.right+18,top:q.top-55,bottom:q.bottom+55};if(pointInRect(x,y,hit)){rackEl.classList.add('dropTarget');return{type:'rack'}}const target=boardTargetAt(x,y);if(target){const cell=boardEl.querySelector(`.cell[data-r=\"${target.r}\"][data-c=\"${target.c}\"]`);cell?.classList.add('dropTarget');return target}return null"
new_target = "const target=boardTargetAt(x,y);if(target){const cell=boardEl.querySelector(`.cell[data-r=\"${target.r}\"][data-c=\"${target.c}\"]`);cell?.classList.add('dropTarget');return target}const q=rackEl.getBoundingClientRect(),hit={left:q.left-18,right:q.right+18,top:q.top-55,bottom:q.bottom+55};if(pointInRect(x,y,hit)){rackEl.classList.add('dropTarget');return{type:'rack'}}return null"
if old_target in game:
    game = game.replace(old_target, new_target, 1)
elif new_target not in game:
    raise SystemExit('Bottom-row priority patch target not found')

# App Review/iPad compatibility: make the PLAY control visibly responsive even
# when a reviewer taps it before placing tiles, and make the drag-first action
# explicit in the first-game instructions.
play_handler = "playButton.onclick=()=>{if(spectatorMode){status.textContent=\"You can view this board, but it’s your opponent’s turn.\";return}if(swapMode)confirmSwap();else playMove()}"
play_handler_fixed = "playButton.onclick=()=>{if(spectatorMode){status.textContent=\"You can view this board, but it’s your opponent’s turn.\";return}if(swapMode){confirmSwap();return}if(!pending.length){status.textContent='Drag a tile from your rack onto the board, then tap PLAY.';alert('To play: drag one or more tiles from your rack onto the board, then tap PLAY.');return}playMove()}"
if play_handler in game:
    game = game.replace(play_handler, play_handler_fixed, 1)
elif play_handler_fixed not in game:
    raise SystemExit('PLAY responsiveness patch target not found')
engine.write_text(game)

# Clarify the first interaction for reviewers and first-time players.
text = index.read_text()
rules_marker = '<div class="rulesWelcomeItems">'
rules_tip = '<div class="rulesWelcomeItem"><div class="rulesIcon rulesIconBlue">↥</div><div><strong>Drag, then play.</strong><span>Drag tiles from your rack onto the board to make a word, then tap PLAY.</span></div></div>'
if rules_tip not in text:
    if rules_marker not in text:
        raise SystemExit('Rules welcome insertion target not found')
    text = text.replace(rules_marker, rules_marker + rules_tip, 1)
index.write_text(text)

app = Path('www/app-v3140.js')
app_text = app.read_text()
if "const deleteAccount=document.getElementById('deleteAccount');" not in app_text:
    marker = "  logoutAccount.onclick=async()=>{"
    if marker not in app_text:
        raise SystemExit('Delete-account JavaScript insertion target not found')
    app_text = app_text.replace(marker, "  const deleteAccount=document.getElementById('deleteAccount');\n\n" + marker, 1)

app_text = app_text.replace("      logoutAccount.classList.remove('hidden');","      logoutAccount.classList.remove('hidden');\n      deleteAccount.classList.remove('hidden');",1)
app_text = app_text.replace("      logoutAccount.classList.add('hidden');","      logoutAccount.classList.add('hidden');\n      deleteAccount.classList.add('hidden');",1)

if 'deleteAccount.onclick=async()=>{' not in app_text:
    auth_marker = '  function authCredentials(){'
    if auth_marker not in app_text:
        raise SystemExit('Delete-account handler target not found')
    handler = '''  deleteAccount.onclick=async()=>{
    if(!confirm('Delete your Yay Everybody account? This permanently deletes your account, profile, games, and associated data. This cannot be undone.')) return;
    if(!confirm('Are you sure? This action cannot be reversed.')) return;
    deleteAccount.disabled=true;
    deleteAccount.textContent='DELETING ACCOUNT…';
    try{
      const {data,error}=await client.functions.invoke('delete-account',{body:{}});
      if(error)throw error;
      if(!data?.ok)throw new Error(data?.error||'Account deletion failed.');
      try{await client.auth.signOut()}catch(e){}
      alert('Your account has been deleted.');
      location.reload();
    }catch(e){
      console.error('Account deletion failed',e);
      alert('We could not delete your account. Please try again.');
      deleteAccount.disabled=false;
      deleteAccount.textContent='DELETE ACCOUNT';
    }
  };

'''
    app_text = app_text.replace(auth_marker, handler + auth_marker, 1)
app.write_text(app_text)


# Scrobble 1.0.1: restrained native haptics.
# Capacitor exposes registered plugins through window.Capacitor.Plugins in this
# packaged app. Calls are deliberately best-effort so the web build still works.
haptic_helper = '''
<script id="scrobble-haptics">
(function(){
  function plugin(){ return window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Haptics; }
  window.ScrobbleHaptics={
    light:function(){ try{ var h=plugin(); if(h) h.impact({style:'LIGHT'}); }catch(e){} },
    medium:function(){ try{ var h=plugin(); if(h) h.impact({style:'MEDIUM'}); }catch(e){} },
    select:function(){ try{ var h=plugin(); if(h) h.selectionStart().then(function(){return h.selectionChanged()}).then(function(){return h.selectionEnd()}); }catch(e){} },
    success:function(){ try{ var h=plugin(); if(h) h.notification({type:'SUCCESS'}); }catch(e){} },
    error:function(){ try{ var h=plugin(); if(h) h.notification({type:'ERROR'}); }catch(e){} }
  };
})();
</script>
'''
text = index.read_text()
if 'id="scrobble-haptics"' not in text:
    text = text.replace('</head>', haptic_helper + '</head>')
index.write_text(text)

# Add tactile feedback without turning every screen tap into a buzz-fest.
engine = Path('www/game-engine-v3140.js')
game = engine.read_text()
haptic_event_patch = '''
;(()=>{
  const H=()=>window.ScrobbleHaptics;
  document.addEventListener('pointerdown',e=>{
    const tile=e.target.closest&&e.target.closest('.tile');
    if(tile) H()?.light();
  },{passive:true});
  document.addEventListener('click',e=>{
    const b=e.target.closest&&e.target.closest('button');
    if(!b||b.disabled)return;
    const t=(b.textContent||'').trim().toUpperCase();
    if(/^(PLAY|SWAP|PASS|SHARE|COPY)/.test(t)) H()?.light();
  },{passive:true});
})();
'''
if 'const H=()=>window.ScrobbleHaptics;' not in game:
    game += haptic_event_patch
engine.write_text(game)


# Scrobble 1.0.1 UI cleanup: progressive disclosure on New Game and Account.
text = index.read_text()
accordion_style = '''
<style id="scrobble-101-accordions">
.scrobble101-choice{width:100%;min-height:52px;margin:8px 0;border:0;border-radius:12px;font-weight:900}
.scrobble101-panel{overflow:hidden;max-height:0;opacity:0;transition:max-height .28s ease,opacity .22s ease,padding .28s ease;padding:0}
.scrobble101-panel.open{max-height:720px;opacity:1;padding:8px 0 14px}
</style>
'''
accordion_script = '''
<script id="scrobble-101-accordion-script">
(function(){
 const H=()=>window.ScrobbleHaptics;
 function setupPair(host, first, second){
   if(!host||!first||!second||first.dataset.scrobble101)return;
   first.dataset.scrobble101=second.dataset.scrobble101='1';
   [first,second].forEach((button,i)=>{
     const panel=document.createElement('div'); panel.className='scrobble101-panel';
     button.parentNode.insertBefore(panel,button.nextSibling);
     let n=panel.nextSibling;
     while(n && n!== (i===0?second:null)){
       const next=n.nextSibling;
       if(n.nodeType===1 && n!==second) panel.appendChild(n);
       n=next;
     }
     button.addEventListener('click',()=>{
       H()?.select();
       const open=!panel.classList.contains('open');
       host.querySelectorAll('.scrobble101-panel.open').forEach(p=>p.classList.remove('open'));
       if(open)panel.classList.add('open');
     });
   });
 }
 function byText(root,re){return [...root.querySelectorAll('button')].find(b=>re.test((b.textContent||'').trim()));}
 function install(){
   // New Game: preserve existing controls/handlers; only reorganize their disclosure.
   const ng=[...document.querySelectorAll('div,section,main')].find(x=>/new game/i.test(x.textContent||'')&&byText(x,/play.*friend/i)&&byText(x,/play.*computer/i));
   if(ng) setupPair(ng,byText(ng,/play.*friend/i),byText(ng,/play.*computer/i));
   // Signed-out Account: Login and Create Account use the same interaction.
   const ac=[...document.querySelectorAll('div,section,main')].find(x=>/account/i.test((x.id||'')+' '+(x.className||'')+' '+(x.textContent||''))&&byText(x,/log ?in/i)&&byText(x,/create.*account/i));
   if(ac) setupPair(ac,byText(ac,/log ?in/i),byText(ac,/create.*account/i));
 }
 document.addEventListener('DOMContentLoaded',()=>setTimeout(install,100));
 new MutationObserver(()=>install()).observe(document.documentElement,{childList:true,subtree:true});
})();
</script>
'''
if 'id="scrobble-101-accordions"' not in text:
    text=text.replace('</head>',accordion_style+'</head>')
if 'id="scrobble-101-accordion-script"' not in text:
    text=text.replace('</body>',accordion_script+'</body>')
index.write_text(text)

# Scrobble 1.0.1 invite URLs and sharing.
app = Path('www/app-v3140.js')
app_text = app.read_text()
# Any invite copied/shared from the packaged capacitor origin must become a public HTTPS URL.
invite_fix = '''
;(()=>{
 const canonicalInvite=(raw)=>{
   try{
     const u=new URL(raw,location.href);
     return 'https://yayeverybody.com'+u.pathname+u.search+u.hash;
   }catch(e){return raw}
 };
 const nativeShare=navigator.share&&navigator.share.bind(navigator);
 if(nativeShare){
   navigator.share=(data)=>{
     const clean=Object.assign({},data||{});
     if(clean.url)clean.url=canonicalInvite(clean.url);
     return nativeShare(clean);
   };
 }
 const nativeWrite=navigator.clipboard&&navigator.clipboard.writeText&&navigator.clipboard.writeText.bind(navigator.clipboard);
 if(nativeWrite){
   navigator.clipboard.writeText=(value)=>nativeWrite(typeof value==='string'?canonicalInvite(value):value);
 }
 window.ScrobbleCanonicalInvite=canonicalInvite;
})();
'''
if 'window.ScrobbleCanonicalInvite=canonicalInvite' not in app_text:
    app_text = invite_fix + app_text
app.write_text(app_text)
