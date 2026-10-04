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

# Detect actual overlap with the blue rack strip before board snap tolerance.
# The fallback tolerance still gives the bottom board row first refusal when
# neither the dragged tile nor the finger has entered the rack strip.
old_target = "const q=rackEl.getBoundingClientRect(),hit={left:q.left-18,right:q.right+18,top:q.top-55,bottom:q.bottom+55};if(pointInRect(x,y,hit)){rackEl.classList.add('dropTarget');return{type:'rack'}}const target=boardTargetAt(x,y);if(target){const cell=boardEl.querySelector(`.cell[data-r=\"${target.r}\"][data-c=\"${target.c}\"]`);cell?.classList.add('dropTarget');return target}return null"
new_target = """const q=rackEl.getBoundingClientRect();
const area=rackEl.closest('.rackarea')||rackEl,ar=area.getBoundingClientRect();
const actions=area.querySelector('.actions')?.getBoundingClientRect();
const row={left:ar.left,right:ar.right,top:ar.top,bottom:actions?.top??q.bottom};
const tile=drag?.ghost?.querySelector('.rackTile')||drag?.ghost;
const tr=tile?.getBoundingClientRect();
const rackOverlap=tr&&tr.width>0&&tr.height>0&&tr.right>row.left&&tr.left<row.right&&tr.bottom>row.top&&tr.top<row.bottom;
if(pointInRect(x,y,row)||rackOverlap){rackEl.classList.add('dropTarget');return{type:'rack'}}
const target=boardTargetAt(x,y);if(target){const cell=boardEl.querySelector(`.cell[data-r="${target.r}"][data-c="${target.c}"]`);cell?.classList.add('dropTarget');return target}
const hit={left:q.left-18,right:q.right+18,top:q.top-55,bottom:q.bottom+55};if(pointInRect(x,y,hit)){rackEl.classList.add('dropTarget');return{type:'rack'}}return null"""
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

# Reuse the exact source-level invite fix proven in Scrobble 1.0.1 (commit
# 9455d48): do not derive invite links from Capacitor's localhost origin.
old_invite_fn = "function inviteURL(code){return location.origin+location.pathname+'?join='+encodeURIComponent(code)}"
new_invite_fn = "function inviteURL(code){return 'https://yayeverybody.com/?join='+encodeURIComponent(code)}"
if old_invite_fn in app_text:
    app_text = app_text.replace(old_invite_fn, new_invite_fn, 1)
elif new_invite_fn not in app_text:
    raise SystemExit('Known Scrobble inviteURL function not found')
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

# iOS invite URL normalization: the web app builds invites from location.href.
# Inside Capacitor that produces capacitor://localhost/?join=..., which is not
# shareable as a Universal Link. Rewrite that URL at the native share boundary
# to the public HTTPS origin.
# Fix invite URL at its source in the packaged app. The web app uses the current
# origin to construct invite links; in Capacitor that origin is capacitor://localhost.
# Replace those origin expressions with the public HTTPS origin before packaging.
for web_file in Path('www').glob('*.js'):
    source = web_file.read_text()
    original = source
    source = source.replace("location.origin+'/?join='", "'https://yayeverybody.com/?join='")
    source = source.replace('location.origin+"/?join="', '"https://yayeverybody.com/?join="')
    source = source.replace("window.location.origin+'/?join='", "'https://yayeverybody.com/?join='")
    source = source.replace('window.location.origin+"/?join="', '"https://yayeverybody.com/?join="')
    source = source.replace("location.href.split('?')[0]+'?join='", "'https://yayeverybody.com/?join='")
    source = source.replace('location.href.split("?")[0]+"?join="', '"https://yayeverybody.com/?join="')
    if source != original:
        web_file.write_text(source)

# iOS invite display/copy hotfix: Capacitor's WebView origin is
# capacitor://localhost, so invite URLs constructed from location.href are wrong
# before the user even reaches the native share sheet. Override the visible/copy
# value at the source by making URL construction use the public origin.
url_origin_script = '''
<script id="scrobble-ios-public-invite-origin">
(()=>{
  if(!window.Capacitor?.isNativePlatform?.()) return;
  const normalize=(value)=>{
    try{
      const u=new URL(String(value));
      if(u.protocol==='capacitor:' && u.hostname==='localhost'){
        return 'https://yayeverybody.com'+u.pathname+u.search+u.hash;
      }
    }catch(e){}
    return value;
  };
  const nativeWriteText=navigator.clipboard?.writeText?.bind(navigator.clipboard);
  if(nativeWriteText){
    navigator.clipboard.writeText=(value)=>nativeWriteText(normalize(value));
  }
  const normalizeDom=()=>{
    document.querySelectorAll('input,textarea,a').forEach(el=>{
      if('value' in el && typeof el.value==='string' && el.value.startsWith('capacitor://localhost/')){
        el.value=normalize(el.value);
      }
      if(el.tagName==='A' && typeof el.href==='string' && el.href.startsWith('capacitor://localhost/')){
        el.href=normalize(el.href);
      }
    });
  };
  normalizeDom();
  new MutationObserver(normalizeDom).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['value','href']});
  document.addEventListener('click',()=>queueMicrotask(normalizeDom),true);
})();
</script>
'''
text = index.read_text()
if 'id="scrobble-ios-public-invite-origin"' not in text:
    text = text.replace('</body>', url_origin_script + '</body>')
index.write_text(text)


# iOS native share hotfix: Web Share can throw a TypeError inside Capacitor's
# WKWebView. Use Capacitor Share when available, while preserving the existing
# web share path as a fallback. Patch navigator.share itself so every existing
# Scrobble invite-share call benefits without changing game logic.
share_bridge = '''
<script type="module" id="scrobble-ios-native-share">
(()=>{
  if(!window.Capacitor?.isNativePlatform?.()) return;
  const NativeShare=window.Capacitor?.Plugins?.Share;
  if(!NativeShare?.share) return;
  const webShare=navigator.share?.bind(navigator);
  try{
    Object.defineProperty(navigator,'share',{
      configurable:true,
      value:async(data={})=>{
        const payload={};
        if(data.title) payload.title=String(data.title);
        if(data.text) payload.text=String(data.text);
        if(data.url){
          let shareUrl=String(data.url);
          try{
            const u=new URL(shareUrl);
            if(u.protocol==='capacitor:' && u.hostname==='localhost'){
              shareUrl='https://yayeverybody.com'+u.pathname+u.search+u.hash;
            }
          }catch(e){}
          payload.url=shareUrl;
        }
        try{
          return await NativeShare.share(payload);
        }catch(err){
          const message=String(err?.message||err||'');
          if(/cancel/i.test(message)) return;
          if(webShare) return webShare(data);
          throw err;
        }
      }
    });
  }catch(e){ console.error('Scrobble native share setup failed',e); }
})();
</script>
'''
text = index.read_text()
if 'id="scrobble-ios-native-share"' not in text:
    text = text.replace('</body>', share_bridge + '</body>')
index.write_text(text)


# iOS Universal Link hotfix: preserve the incoming invite URL inside the
# Capacitor WebView. Existing Scrobble invite parsing can then consume the
# same path/query/hash it receives on the website.
deep_link_script = '''
<script type="module" id="scrobble-ios-universal-links">
(async()=>{
  if(!window.Capacitor?.isNativePlatform?.()) return;
  try{
    const App = window.Capacitor?.Plugins?.App;
    if(!App) throw new Error('Capacitor App plugin unavailable');
    let routing=false;
    let lastJoin='';
    const routeInvite=(incoming)=>{
      try{
        const u=new URL(incoming);
        if(!/(^|\\.)yayeverybody\\.com$/i.test(u.hostname)) return;
        const join=u.searchParams.get('join');
        if(!join) return;
        // Allow a different invite while the app is already running. The old
        // boolean latch incorrectly ignored every invite after the first one.
        if(routing && join===lastJoin) return;
        routing=true;
        lastJoin=join;
        // Do not reload the Capacitor WebView. Reloading caused the launch URL
        // to be returned again on startup, creating an infinite splash/white-screen loop.
        const next='/?join='+encodeURIComponent(join);
        history.replaceState({},'',next);
        // Scrobble's bootstrap owns the actual invite acceptance/join flow.
        // Re-running app-v3140.js on a live page duplicates module state and can
        // leave the board showing the new invite while the join/save handlers
        // still belong to the previous game (especially with crossed invites).
        // Give the existing app a clean web-document bootstrap instead. This is
        // a WebView navigation, not a native-app relaunch, so App.getLaunchUrl()
        // is not re-consumed and the old splash/white-screen loop is avoided.
        sessionStorage.setItem('scrobbleNativeJoin',join);
        location.replace(next);
      }catch(e){
        routing=false;
        console.error('Scrobble invite URL error',e);
      }
    };
    const launch=await App.getLaunchUrl();
    if(launch?.url) routeInvite(launch.url);
    App.addListener('appUrlOpen',({url})=>routeInvite(url));
  }catch(e){ console.error('Scrobble universal-link setup failed',e); }
})();
</script>
'''
text = index.read_text()
if 'id="scrobble-ios-universal-links"' not in text:
    text = text.replace('</body>', deep_link_script + '</body>')
index.write_text(text)

# Clean app-flow controller: keep the original auth DOM/handlers intact and only
# present modes by CSS. No replacement auth fields, capture interception, or polling.
text=index.read_text()
account_css='''
<style id="scrobble-clean-auth-ui">
#accountBox.scrobbleLoginMode label[for="accountUsername"],#accountBox.scrobbleLoginMode #accountUsername,#accountBox.scrobbleLoginMode .usernameHint,#accountBox.scrobbleLoginMode #createAccount,#accountBox.scrobbleLoginMode #accountIdentity{display:none!important}
#accountBox.scrobbleCreateMode #signInAccount,#accountBox.scrobbleCreateMode #forgotPassword{display:none!important}
#scrobbleWelcome{position:fixed;inset:0;z-index:2147483000;background:linear-gradient(180deg,#1699dc,#0877bb 58%,#064b82);display:flex;align-items:center;justify-content:center;padding:24px}#scrobbleWelcome.hidden{display:none!important}#scrobbleWelcome>div{width:min(100%,430px);text-align:center;color:#fff}#scrobbleWelcome h1{font-size:36px;margin:0 0 12px}#scrobbleWelcome p{font-size:18px;margin:0 0 28px}#scrobbleWelcome button{width:100%;min-height:58px;margin:7px 0;border-radius:14px;border:2px solid #fff;font-weight:900;font-size:16px}#scrobbleWelcomeCreate{background:#f2bd45;border-color:#f2bd45!important;color:#173044}#scrobbleWelcomeLogin{background:transparent;color:#fff}
</style>'''
welcome='''<div id="scrobbleWelcome" class="hidden"><div><h1>Welcome to Scrobble</h1><p>Play words with friends and family. Your games stay with you.</p><button id="scrobbleWelcomeCreate" type="button">CREATE ACCOUNT</button><button id="scrobbleWelcomeLogin" type="button">LOG IN</button></div></div><script id="scrobble-clean-auth-controller">(()=>{const w=document.getElementById('scrobbleWelcome'),a=document.getElementById('accountBox'),logout=document.getElementById('logoutAccount');if(!w||!a)return;const open=mode=>{w.classList.add('hidden');a.classList.remove('hidden');a.classList.toggle('scrobbleLoginMode',mode==='login');a.classList.toggle('scrobbleCreateMode',mode==='create');const h=[...a.querySelectorAll('h1,h2,h3')].find(x=>/account/i.test(x.textContent||''));if(h)h.textContent=mode==='login'?'Welcome Back!':'Create Your Scrobble Account'};document.getElementById('scrobbleWelcomeLogin').onclick=()=>open('login');document.getElementById('scrobbleWelcomeCreate').onclick=()=>open('create');let n=0;const decide=()=>{if(logout&&!logout.classList.contains('hidden')){w.classList.add('hidden');return}if(++n<40){setTimeout(decide,125);return}if(!new URLSearchParams(location.search).get('join'))w.classList.remove('hidden')};decide()})();</script>'''
if 'id="scrobble-clean-auth-ui"' not in text:text=text.replace('</head>',account_css+'</head>',1)
if 'id="scrobbleWelcome"' not in text:text=text.replace('</body>',welcome+'</body>',1)
index.write_text(text)

# Build-time invariants: the original auth form and handlers are the source of truth.
final_index=index.read_text(); final_app=Path('www/app-v3140.js').read_text()
assert 'USERNAME <span style="font-weight:500">(NEW ACCOUNTS)</span>' in final_index, 'Original auth DOM changed'
assert 'signInAccount.onclick' in final_app and 'createAccount.onclick' in final_app and 'forgotPassword.onclick' in final_app, 'Original auth handlers changed'
assert 'loginAccountPanel' not in final_index and 'accountCreateEmail' not in final_index, 'Split auth DOM must not exist'
assert 'scrobble-approved-new-game-controller' not in final_index, 'Fallback game controller must not exist'

# Progressive New Game presentation. Preserve createGame/createComputerGame;
# this patch only changes the modal DOM and delegates back to those functions.
text=index.read_text()
old_game='''    <button id="playFriendMode" class="modePrimary" type="button">PLAY A FRIEND</button>
    <div class="weirdBox">
      <div class="weirdTitle">MAKE IT WEIRD</div>
      <div class="weirdSub">Optional. Choose one.</div>
      <label class="weirdChoice"><input type="checkbox" value="all_or_none"><span><strong>All or None</strong><small>Only A, L, O, R, N and E tiles.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="vowel_movement"><span><strong>Vowel Movement</strong><small>Other letters are traded for extra vowels.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="high_roller"><span><strong>High Roller</strong><small>J, Q, X and Z are worth triple.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="too_many_tiles"><span><strong>Too Many Tiles</strong><small>Play with 9 tiles instead of 7.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="oops_all_ys"><span><strong>Oops! All Y’s</strong><small>Replace 20 other tiles with Y’s.</small></span></label>
    </div>
    <div class="modeDivider"><span>OR PLAY THE COMPUTER</span></div>
    <div class="cpuChoices">
      <button type="button" data-cpu-difficulty="easy"><strong>EASY</strong><span>Relaxed opponent</span></button>
      <button type="button" data-cpu-difficulty="medium"><strong>MEDIUM</strong><span>Competitive opponent</span></button>
      <button type="button" data-cpu-difficulty="hard"><strong>HARD</strong><span>Best move it can find</span></button>
    </div>'''
new_game='''    <div class="modeChooser">
      <button id="playFriendMode" class="modeChoice" type="button">PLAY A FRIEND</button>
      <button id="playComputerMode" class="modeChoice" type="button">PLAY THE COMPUTER</button>
    </div>
    <div id="sharedWeirdBox" class="weirdBox hidden">
      <div class="weirdTitle">MAKE IT WEIRD</div><div class="weirdSub">Optional. Choose one.</div>
      <label class="weirdChoice"><input type="checkbox" value="all_or_none"><span><strong>All or None</strong><small>Only A, L, O, R, N and E tiles.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="vowel_movement"><span><strong>Vowel Movement</strong><small>Other letters are traded for extra vowels.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="high_roller"><span><strong>High Roller</strong><small>J, Q, X and Z are worth triple.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="too_many_tiles"><span><strong>Too Many Tiles</strong><small>Play with 9 tiles instead of 7.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="oops_all_ys"><span><strong>Oops! All Y’s</strong><small>Replace 20 other tiles with Y’s.</small></span></label>
    </div>
    <div id="friendModePanel" class="modePanel hidden"><button id="startFriendGame" class="friendStart" type="button">CREATE GAME</button></div>
    <div id="computerModePanel" class="modePanel hidden"><div class="cpuChoices">
      <button type="button" data-cpu-difficulty="easy"><strong>EASY</strong><span>Relaxed opponent</span></button>
      <button type="button" data-cpu-difficulty="medium"><strong>MEDIUM</strong><span>Competitive opponent</span></button>
      <button type="button" data-cpu-difficulty="hard"><strong>HARD</strong><span>Best move it can find</span></button>
    </div></div>'''
if old_game not in text: raise SystemExit('Stable New Game source block not found')
text=text.replace(old_game,new_game,1)
text=text.replace('<h2>Invite a player</h2>', '<h2>Invite a friend</h2>', 1)
flow_style='''<style id="scrobble-clean-game-flow">#gameModeBox .modeChooser{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}#gameModeBox .modeChoice{min-height:58px;border:2px solid #f2bd45;border-radius:14px;background:#0b4c7c;color:#fff;font-weight:900;padding:9px}#gameModeBox .modeChoice.active{background:#f2bd45;color:#173044}#gameModeBox .modePanel.hidden,#gameModeBox #sharedWeirdBox.hidden{display:none!important}#gameModeBox .friendStart{width:100%;min-height:54px;margin:8px 0 12px;border:0;border-radius:14px;background:#f2bd45;color:#173044;font-weight:900}#gameModeBox .gameModeCard{max-height:calc(100dvh - 36px - env(safe-area-inset-top) - env(safe-area-inset-bottom));overflow-y:auto}#gameModeBox #startFriendGame.hidden{display:none!important}#friendModePanel #inviteBox{position:static;inset:auto;z-index:auto;background:transparent;display:block;padding:0}#friendModePanel #inviteBox.hidden{display:none!important}#friendModePanel #inviteBox .inviteCard{width:100%;box-sizing:border-box;background:transparent;border-radius:0;padding:12px 0 0}#friendModePanel #inviteBox h2{font-size:22px}#friendModePanel #inviteBox p{color:#e5f3ff!important;font-size:14px;line-height:1.45}#friendModePanel #inviteLink{color:#173044!important;background:#f3f5f6!important;font-size:12px;overflow-wrap:anywhere}#friendModePanel #inviteBox button{min-height:48px}#inviteBox #copyInvite{background:#0878be!important;color:#fff!important}#inviteBox #shareInvite{background:#f2bd45!important;color:#173044!important}</style>'''
text=text.replace('</head>',flow_style+'</head>',1); index.write_text(text)

app=Path('www/app-v3140.js'); js=app.read_text()
old_handlers="  document.getElementById('newGameDash').onclick=()=>gameModeBox.classList.remove('hidden');\n  closeGameMode.onclick=()=>gameModeBox.classList.add('hidden');\n  gameModeBox.addEventListener('click',e=>{if(e.target===gameModeBox)gameModeBox.classList.add('hidden')});\n  playFriendMode.onclick=()=>{gameModeBox.classList.add('hidden');createGame()};\n  gameModeBox.querySelectorAll('[data-cpu-difficulty]').forEach(btn=>btn.onclick=()=>createComputerGame(btn.dataset.cpuDifficulty));"
new_handlers="""  const playComputerMode=document.getElementById('playComputerMode'),friendModePanel=document.getElementById('friendModePanel'),computerModePanel=document.getElementById('computerModePanel'),startFriendGame=document.getElementById('startFriendGame'),sharedWeirdBox=document.getElementById('sharedWeirdBox');
  const inviteHome=inviteBox.parentNode;
  function resetFriendInvite(){
    inviteBox.classList.add('hidden');
    inviteHome.appendChild(inviteBox);
    startFriendGame.classList.remove('hidden');
    pendingNewGame=null;
  }
  function setGameMode(mode){
    const friend=mode==='friend';
    if(!friend && friendModePanel.contains(inviteBox))resetFriendInvite();
    const inviting=friend && friendModePanel.contains(inviteBox);
    friendModePanel.classList.toggle('hidden',!friend);
    computerModePanel.classList.toggle('hidden',friend);
    sharedWeirdBox.classList.toggle('hidden',inviting);
    playFriendMode.classList.toggle('active',friend);
    playComputerMode.classList.toggle('active',!friend);
    document.getElementById('gameModeTitle').textContent=friend?'Play a Friend':'Play the Computer';
  }
  function openGameMode(){
    resetFriendInvite();
    friendModePanel.classList.add('hidden');
    computerModePanel.classList.add('hidden');
    sharedWeirdBox.classList.add('hidden');
    sharedWeirdBox.querySelectorAll('input').forEach(x=>x.checked=false);
    playFriendMode.classList.remove('active');
    playComputerMode.classList.remove('active');
    document.getElementById('gameModeTitle').textContent='New Game';
    gameModeBox.classList.remove('hidden');
  }
  function closeGameModeScreen(){
    gameModeBox.classList.add('hidden');
    if(friendModePanel.contains(inviteBox))resetFriendInvite();
  }
  document.getElementById('newGameDash').onclick=openGameMode;
  closeGameMode.onclick=closeGameModeScreen;
  gameModeBox.addEventListener('click',e=>{if(e.target===gameModeBox)closeGameModeScreen()});
  playFriendMode.onclick=()=>setGameMode('friend');
  playComputerMode.onclick=()=>setGameMode('computer');
  startFriendGame.onclick=()=>createGame();
  gameModeBox.querySelectorAll('[data-cpu-difficulty]').forEach(btn=>btn.onclick=()=>createComputerGame(btn.dataset.cpuDifficulty));"""
if old_handlers not in js: raise SystemExit('Stable packaged New Game handlers not found; refusing fallback')
js=js.replace(old_handlers,new_handlers,1)

# Reuse the same invite element and its original copy/share handlers inline.
# Existing waiting-game invites still use the standalone presentation.
old_invite_show = "    inviteBox.classList.remove('hidden')"
new_invite_show = """    if(newGameState && !gameModeBox.classList.contains('hidden')){
      friendModePanel.appendChild(inviteBox);
      sharedWeirdBox.classList.add('hidden');
      startFriendGame.classList.add('hidden');
    }else{
      inviteHome.appendChild(inviteBox);
      gameModeBox.classList.add('hidden');
    }
    inviteBox.classList.remove('hidden')"""
if js.count(old_invite_show) != 1:
    raise SystemExit('Expected exactly one invite presentation target')
js=js.replace(old_invite_show,new_invite_show,1)
old_invite_close = "  function closeInviteBox(){inviteBox.classList.add('hidden');pendingNewGame=null}"
new_invite_close = """  function closeInviteBox(){
    const inline=friendModePanel.contains(inviteBox);
    resetFriendInvite();
    if(inline)gameModeBox.classList.add('hidden');
  }"""
if old_invite_close not in js:
    raise SystemExit('Expected original invite close handler')
js=js.replace(old_invite_close,new_invite_close,1)
app.write_text(js)

final_index=index.read_text(); final_app=app.read_text()
assert 'id="playComputerMode"' in final_index and 'id="startFriendGame"' in final_index
assert 'OR PLAY THE COMPUTER' not in final_index
assert "startFriendGame.onclick=()=>createGame()" in final_app
assert "btn.onclick=()=>createComputerGame(btn.dataset.cpuDifficulty)" in final_app
assert new_invite_show in final_app
assert 'scrobble-approved-new-game-controller' not in final_index

# Load the native feedback adapter without replacing any game/UI handlers.
haptics_source=Path(__file__).with_name('scrobble-haptics.js')
Path('www/scrobble-haptics.js').write_text(haptics_source.read_text())
text=index.read_text()
text=text.replace('</body>', '<script src="scrobble-haptics.js"></script></body>', 1)
index.write_text(text)

# Drive feedback from the actual score animation, including cancellation.
engine=Path('www/game-engine-v3140.js')
game=engine.read_text()
start=game.index('function animateScoreValue(')
end=game.index('\nfunction render()', start)
score=game[start:end]
score_hooks={
    "  target=Number(target)||0;": "  target=Number(target)||0;\n  window.ScrobbleHaptics?.scoreCancel?.(slot);",
    "  const started=performance.now();": "  const started=performance.now();\n  window.ScrobbleHaptics?.scoreStart?.(slot,target-current);",
    "    const p=Math.min(1,(now-started)/duration);": "    const p=Math.min(1,(now-started)/duration);\n    window.ScrobbleHaptics?.scoreProgress?.(slot,p,now);",
    "      displayedScores[slot]=target;": "      displayedScores[slot]=target;\n      window.ScrobbleHaptics?.scoreEnd?.(slot);",
}
for old,new in score_hooks.items():
    if score.count(old)!=1:
        raise SystemExit('Expected original score animation hook: '+old)
    score=score.replace(old,new,1)
game=game[:start]+score+game[end:]
engine.write_text(game)
