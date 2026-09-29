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





# Haptics bridge + diagnostic. Keep this observable during TestFlight validation:
# a long press on the SCROBBLE wordmark fires a native MEDIUM impact and briefly
# shows HAPTIC TEST. Once device validation passes, gameplay hooks can use the
# same bridge and this diagnostic can be removed.
haptic_helper = r'''
<script id="scrobble-haptics">
(()=>{
  const plugin=()=>window.Capacitor?.Plugins?.Haptics;
  async function impact(style='LIGHT'){
    const h=plugin();
    if(!h?.impact) throw new Error('Capacitor Haptics plugin unavailable');
    await h.impact({style});
    return true;
  }
  window.ScrobbleHaptics={impact,light:()=>impact('LIGHT'),medium:()=>impact('MEDIUM'),heavy:()=>impact('HEAVY')};

  let timer;
  document.addEventListener('pointerdown',e=>{
    const target=e.target.closest?.('.brand,.logo,[class*="logo"],[id*="logo"]');
    if(!target || !/SCROBBLE/i.test(target.textContent||'')) return;
    timer=setTimeout(async()=>{
      try{
        await impact('MEDIUM');
        const old=target.textContent;
        target.textContent='HAPTIC TEST';
        setTimeout(()=>{target.textContent=old},700);
      }catch(err){
        console.error('SCROBBLE HAPTIC DIAGNOSTIC FAILED',err);
        alert('Haptic test failed: '+err.message);
      }
    },650);
  },{passive:true});
  for(const ev of ['pointerup','pointercancel','pointermove']) document.addEventListener(ev,()=>clearTimeout(timer),{passive:true});
})();
</script>
'''
text = index.read_text()
if 'id="scrobble-haptics"' not in text:
    text = text.replace('</body>',haptic_helper+'</body>',1)
index.write_text(text)

# Games-page cleanup: progressively disclose friend/computer setup instead of
# showing every option at once. Keep "Make It Weird" inside the chosen mode.
text = index.read_text()
old_game = '''    <button id="playFriendMode" class="modePrimary" type="button">PLAY A FRIEND</button>
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
weird = '''<div class="weirdBox">
        <div class="weirdTitle">MAKE IT WEIRD</div>
        <div class="weirdSub">Optional. Choose one.</div>
        <label class="weirdChoice"><input type="checkbox" value="all_or_none"><span><strong>All or None</strong><small>Only A, L, O, R, N and E tiles.</small></span></label>
        <label class="weirdChoice"><input type="checkbox" value="vowel_movement"><span><strong>Vowel Movement</strong><small>Other letters are traded for extra vowels.</small></span></label>
        <label class="weirdChoice"><input type="checkbox" value="high_roller"><span><strong>High Roller</strong><small>J, Q, X and Z are worth triple.</small></span></label>
        <label class="weirdChoice"><input type="checkbox" value="too_many_tiles"><span><strong>Too Many Tiles</strong><small>Play with 9 tiles instead of 7.</small></span></label>
        <label class="weirdChoice"><input type="checkbox" value="oops_all_ys"><span><strong>Oops! All Y’s</strong><small>Replace 20 other tiles with Y’s.</small></span></label>
      </div>'''
new_game = f'''    <div class="modeChooser"><button id="playFriendMode" class="modeChoice" type="button">PLAY A FRIEND</button><button id="playComputerMode" class="modeChoice" type="button">PLAY THE COMPUTER</button></div>
    <div id="friendModePanel" class="modePanel hidden">
      {weird}
      <button id="startFriendGame" class="friendStart" type="button">SHARE INVITE</button>
    </div>
    <div id="computerModePanel" class="modePanel hidden">
      <div class="cpuChoices">
        <button type="button" data-cpu-difficulty="easy"><strong>EASY</strong><span>Relaxed opponent</span></button>
        <button type="button" data-cpu-difficulty="medium"><strong>MEDIUM</strong><span>Competitive opponent</span></button>
        <button type="button" data-cpu-difficulty="hard"><strong>HARD</strong><span>Best move it can find</span></button>
      </div>
      {weird}
    </div>'''
if old_game in text:
    text = text.replace(old_game,new_game,1)
elif 'id="playComputerMode"' not in text:
    raise SystemExit('New Game source block not found')

flow_style = '''
<style id="scrobble-game-flow-cleanup">
#gameModeBox .modeChooser{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}
#gameModeBox .modeChoice{min-height:52px;border:2px solid #0d80cd;border-radius:12px;background:#fff;color:#0d80cd;font-weight:900;padding:8px}
#gameModeBox .modeChoice.active{background:#0d80cd;color:#fff}
#gameModeBox .modePanel.hidden{display:none!important}
#gameModeBox .friendStart{width:100%;min-height:50px;margin-top:12px;border:0;border-radius:12px;background:#0d80cd;color:#fff;font-weight:900}
</style>
'''
if 'id="scrobble-game-flow-cleanup"' not in text:
    text = text.replace('</head>',flow_style+'</head>',1)
index.write_text(text)

app = Path('www/app-v3140.js')
js = app.read_text()
old_handlers = "  document.getElementById('newGameDash').onclick=()=>gameModeBox.classList.remove('hidden');\\n  closeGameMode.onclick=()=>gameModeBox.classList.add('hidden');\\n  gameModeBox.addEventListener('click',e=>{if(e.target===gameModeBox)gameModeBox.classList.add('hidden')});\\n  playFriendMode.onclick=()=>{gameModeBox.classList.add('hidden');createGame()};\\n  gameModeBox.querySelectorAll('[data-cpu-difficulty]').forEach(btn=>btn.onclick=()=>createComputerGame(btn.dataset.cpuDifficulty));"
new_handlers = "  const playComputerMode=document.getElementById('playComputerMode'),friendModePanel=document.getElementById('friendModePanel'),computerModePanel=document.getElementById('computerModePanel'),startFriendGame=document.getElementById('startFriendGame');\\n  function setGameMode(mode){const friend=mode==='friend';friendModePanel.classList.toggle('hidden',!friend);computerModePanel.classList.toggle('hidden',friend);playFriendMode.classList.toggle('active',friend);playComputerMode.classList.toggle('active',!friend)}\\n  function openGameMode(){friendModePanel.classList.add('hidden');computerModePanel.classList.add('hidden');playFriendMode.classList.remove('active');playComputerMode.classList.remove('active');gameModeBox.classList.remove('hidden')}\\n  document.getElementById('newGameDash').onclick=openGameMode;\\n  closeGameMode.onclick=()=>gameModeBox.classList.add('hidden');\\n  gameModeBox.addEventListener('click',e=>{if(e.target===gameModeBox)gameModeBox.classList.add('hidden')});\\n  playFriendMode.onclick=()=>setGameMode('friend');playComputerMode.onclick=()=>setGameMode('computer');startFriendGame.onclick=()=>{gameModeBox.classList.add('hidden');createGame()};\\n  gameModeBox.querySelectorAll('[data-cpu-difficulty]').forEach(btn=>btn.onclick=()=>createComputerGame(btn.dataset.cpuDifficulty));"
if old_handlers in js:
    js = js.replace(old_handlers,new_handlers,1)
elif "const playComputerMode=document.getElementById('playComputerMode')" not in js:
    raise SystemExit('New Game JS handlers not found')
app.write_text(js)

# Branded startup splash. iOS still provides the native launch screen while the
# process starts; this in-app layer makes the Scrobble brand visible long enough
# to register, then hands off without delaying returning players unnecessarily.
splash = r'''
<style id="scrobble-startup-splash-style">
#scrobbleStartupSplash{position:fixed;inset:0;z-index:2147483646;background:linear-gradient(180deg,#1699dc 0%,#0877bb 58%,#064b82 100%);display:flex;align-items:center;justify-content:center;opacity:1;transition:opacity .22s ease;font-family:Arial,Helvetica,sans-serif}
#scrobbleStartupSplash.dismiss{opacity:0;pointer-events:none}
#scrobbleStartupSplash .splashInner{text-align:center;padding:28px}
#scrobbleStartupSplash .splashLogo{font-size:clamp(36px,10vw,58px);font-weight:1000;letter-spacing:.06em;color:#f4c052;text-shadow:0 3px 0 #704611,0 5px 14px rgba(0,0,0,.28)}
#scrobbleStartupSplash .splashStudio{margin-top:14px;color:#fff;font-size:14px;font-weight:800;letter-spacing:.28em}
</style>
<div id="scrobbleStartupSplash" aria-hidden="true">
  <div class="splashInner">
    <div class="splashLogo">SCROBBLE</div>
    <div class="splashStudio">YAY EVERYBODY GAMES</div>
  </div>
</div>
<script id="scrobble-startup-splash-script">
(()=>{
  const splash=document.getElementById('scrobbleStartupSplash');
  if(!splash) return;
  const started=performance.now();
  // First launch gets enough time for the brand to register. Returning launches
  // remain quick; never hold the UI beyond 1.25 seconds.
  const minVisible=sessionStorage.getItem('scrobbleSplashSeen') ? 450 : 1050;
  sessionStorage.setItem('scrobbleSplashSeen','1');
  const finish=()=>{
    const wait=Math.max(0,minVisible-(performance.now()-started));
    setTimeout(()=>{
      splash.classList.add('dismiss');
      setTimeout(()=>splash.remove(),240);
    },wait);
  };
  if(document.readyState==='complete') finish();
  else window.addEventListener('load',finish,{once:true});
  setTimeout(finish,1250);
})();
</script>
'''
text = index.read_text()
if 'id="scrobbleStartupSplash"' not in text:
    text = text.replace('<body>', '<body>' + splash)
index.write_text(text)

# Next-release onboarding: replace the dense combined auth/profile screen with a
# simple choice first. Existing authenticated users never see this overlay.
onboarding = r'''
<style id="scrobble-onboarding-v2-style">
#scrobbleOnboardingV2{position:fixed;inset:0;z-index:2147483000;background:linear-gradient(180deg,#1699dc 0%,#0877bb 58%,#064b82 100%);display:flex;align-items:center;justify-content:center;padding:calc(env(safe-area-inset-top) + 22px) 22px calc(env(safe-area-inset-bottom) + 22px);font-family:Arial,Helvetica,sans-serif}
#scrobbleOnboardingV2.hidden{display:none!important}
#scrobbleOnboardingV2 .obCard{width:min(100%,430px);background:#fff;border-radius:28px;padding:34px 26px 28px;box-shadow:0 24px 70px rgba(0,0,0,.25);text-align:center}
#scrobbleOnboardingV2 h1{margin:0 0 10px;color:#16232d;font-size:36px;line-height:1.04}
#scrobbleOnboardingV2 p{margin:0 0 28px;color:#65727b;font-size:18px;line-height:1.35}
#scrobbleOnboardingV2 .obActions{display:flex;gap:12px}
#scrobbleOnboardingV2 button{flex:1;min-height:58px;border-radius:14px;border:2px solid #1488cf;background:#fff;color:#1179b8;font-size:16px;font-weight:900;padding:10px}
#scrobbleOnboardingV2 button.primary{background:#1488cf;color:#fff}
@media(max-width:360px){#scrobbleOnboardingV2 .obActions{flex-direction:column}}
</style>
<div id="scrobbleOnboardingV2" class="hidden" role="dialog" aria-modal="true" aria-labelledby="scrobbleWelcomeTitle">
  <div class="obCard">
    <h1 id="scrobbleWelcomeTitle">Welcome to Scrobble</h1>
    <p>Play words with friends and family. Your games stay with you.</p>
    <div class="obActions">
      <button id="scrobbleCreateChoice" class="primary" type="button">CREATE ACCOUNT</button>
      <button id="scrobbleLoginChoice" type="button">LOG IN</button>
    </div>
  </div>
</div>
<script id="scrobble-onboarding-v2-script">
(()=>{
  const overlay=document.getElementById('scrobbleOnboardingV2');
  const account=document.getElementById('accountBox');
  if(!overlay||!account) return;
  const createBtn=document.getElementById('scrobbleCreateChoice');
  const loginBtn=document.getElementById('scrobbleLoginChoice');
  const signIn=document.getElementById('signInAccount');
  const create=document.getElementById('createAccount');
  const username=document.getElementById('accountUsername');
  const photo=account.querySelector('input[type="file"]')?.closest('div');

  const signedIn=()=>{
    const logout=document.getElementById('logoutAccount');
    return !!logout && !logout.classList.contains('hidden');
  };
  const showAccount=(mode)=>{
    overlay.classList.add('hidden');
    account.classList.remove('hidden');
    if(mode==='login'){
      if(username) username.closest('label,div')?.classList.add('scrobbleCreateOnly');
      if(create) create.style.display='none';
      if(signIn) signIn.style.display='';
    }else{
      if(username) username.closest('label,div')?.classList.remove('scrobbleCreateOnly');
      if(signIn) signIn.style.display='none';
      if(create) create.style.display='';
    }
    // Photo belongs after successful account creation, not before it.
    if(photo) photo.style.display='none';
  };
  createBtn.onclick=()=>showAccount('create');
  loginBtn.onclick=()=>showAccount('login');

  // Auth initialization is async. Wait briefly for the existing app to restore
  // a session; only unauthenticated users get first-run onboarding.
  let checks=0;
  const decide=()=>{
    if(signedIn()){ overlay.classList.add('hidden'); return; }
    if(++checks<12){ setTimeout(decide,125); return; }
    // Do not cover an invite while Scrobble is resolving it; the normal auth
    // flow can request credentials if the invite requires them.
    if(!new URLSearchParams(location.search).get('join')) overlay.classList.remove('hidden');
  };
  decide();
})();
</script>
'''
text = index.read_text()
if 'id="scrobbleOnboardingV2"' not in text:
    text = text.replace('</body>', onboarding + '</body>')
index.write_text(text)

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

# Build-time regression checks for invite/deep-link behavior. These deliberately
# fail the release build if a future edit brings back Capacitor localhost invite
# URLs, script re-bootstrap, or omits the public HTTPS invite function.
app_source = app.read_text()
index_source = index.read_text()
assert "function inviteURL(code){return 'https://yayeverybody.com/?join='+encodeURIComponent(code)}" in app_source, "Public inviteURL regression"
assert "capacitor://localhost/?join=" not in app_source, "Native localhost invite URL regression"
assert "location.replace(next);" in index_source, "Universal Link must clean-bootstrap exact invite"
assert "script.src='app-v3140.js?nativejoin='" not in index_source, "Unsafe live script re-bootstrap returned"
assert "App.addListener('appUrlOpen'" in index_source, "Warm-app Universal Link listener missing"
assert "App.getLaunchUrl()" in index_source, "Cold-launch Universal Link handling missing"


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
        // Ignore an exact duplicate callback only while it is being routed.
        // Once the destination document has loaded, the same invite must remain
        // usable later (for example after the player visits Games and taps the
        // invite again).
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
