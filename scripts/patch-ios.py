from pathlib import Path
import re

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
    try{ const h=plugin(); if(h?.impact) await h.impact({style}); }catch(e){ console.warn('Scrobble haptic skipped',e); }
  }
  async function selection(){
    try{ const h=plugin(); if(h?.selectionStart){await h.selectionStart();await h.selectionChanged();await h.selectionEnd();} else await impact('LIGHT'); }catch(e){}
  }
  window.ScrobbleHaptics={impact,selection,light:()=>impact('LIGHT'),medium:()=>impact('MEDIUM'),heavy:()=>impact('HEAVY')};
  document.addEventListener('pointerup',e=>{
    const el=e.target.closest?.('button,[role="button"],.tile,.rackTile,.weirdChoice');
    if(!el || el.disabled) return;
    const label=(el.textContent||'').trim().toUpperCase();
    if(/^(PLAY|SHARE INVITE|SWAP|PASS)/.test(label)) impact('MEDIUM');
    else selection();
  },{passive:true});
})();
</script>
'''
text = index.read_text()
if 'id="scrobble-haptics"' not in text:
    text = text.replace('</body>',haptic_helper+'</body>',1)
index.write_text(text)

# Approved New Game progressive flow. Preserve the proven createGame() and
# createComputerGame() functions; only change which controls reveal/call them.
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
weird = '''<div id="sharedWeirdBox" class="weirdBox hidden">
      <div class="weirdTitle">MAKE IT WEIRD</div>
      <div class="weirdSub">Optional. Choose one.</div>
      <label class="weirdChoice"><input type="checkbox" value="all_or_none"><span><strong>All or None</strong><small>Only A, L, O, R, N and E tiles.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="vowel_movement"><span><strong>Vowel Movement</strong><small>Other letters are traded for extra vowels.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="high_roller"><span><strong>High Roller</strong><small>J, Q, X and Z are worth triple.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="too_many_tiles"><span><strong>Too Many Tiles</strong><small>Play with 9 tiles instead of 7.</small></span></label>
      <label class="weirdChoice"><input type="checkbox" value="oops_all_ys"><span><strong>Oops! All Y’s</strong><small>Replace 20 other tiles with Y’s.</small></span></label>
    </div>'''
new_game = f'''    <div class="modeChooser">
      <button id="playFriendMode" class="modeChoice" type="button">PLAY A FRIEND</button>
      <button id="playComputerMode" class="modeChoice" type="button">PLAY THE COMPUTER</button>
    </div>
    <div id="friendModePanel" class="modePanel hidden">
      <button id="startFriendGame" class="friendStart" type="button">SHARE INVITE</button>
    </div>
    {weird}
    <div id="computerModePanel" class="modePanel hidden">
      <div class="cpuChoices">
        <button type="button" data-cpu-difficulty="easy"><strong>EASY</strong><span>Relaxed opponent</span></button>
        <button type="button" data-cpu-difficulty="medium"><strong>MEDIUM</strong><span>Competitive opponent</span></button>
        <button type="button" data-cpu-difficulty="hard"><strong>HARD</strong><span>Best move it can find</span></button>
      </div>
    </div>'''
if old_game in text:
    text = text.replace(old_game,new_game,1)
elif 'id="playComputerMode"' not in text:
    raise SystemExit('Approved New Game source block not found')

flow_style = '''
<style id="scrobble-game-flow-approved">
#gameModeBox .modeChooser{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}
#gameModeBox .modeChoice{min-height:58px;border:2px solid #f2bd45;border-radius:14px;background:#0b4c7c;color:#fff;font-weight:900;padding:9px}
#gameModeBox .modeChoice.active{background:#f2bd45;color:#173044}
#gameModeBox .modePanel.hidden,#gameModeBox #sharedWeirdBox.hidden{display:none!important}
#gameModeBox .friendStart{width:100%;min-height:54px;margin:4px 0 12px;border:0;border-radius:14px;background:#f2bd45;color:#173044;font-weight:900}
#gameModeBox .cpuChoices{margin:4px 0 12px}
</style>
'''
if 'id="scrobble-game-flow-approved"' not in text:
    text = text.replace('</head>',flow_style+'</head>',1)
index.write_text(text)

app = Path('www/app-v3140.js')
js = app.read_text()
old_handlers = "  document.getElementById('newGameDash').onclick=()=>gameModeBox.classList.remove('hidden');\\n  closeGameMode.onclick=()=>gameModeBox.classList.add('hidden');\\n  gameModeBox.addEventListener('click',e=>{if(e.target===gameModeBox)gameModeBox.classList.add('hidden')});\\n  playFriendMode.onclick=()=>{gameModeBox.classList.add('hidden');createGame()};\\n  gameModeBox.querySelectorAll('[data-cpu-difficulty]').forEach(btn=>btn.onclick=()=>createComputerGame(btn.dataset.cpuDifficulty));"
new_handlers = '''  const playComputerMode=document.getElementById('playComputerMode'),friendModePanel=document.getElementById('friendModePanel'),computerModePanel=document.getElementById('computerModePanel'),startFriendGame=document.getElementById('startFriendGame'),sharedWeirdBox=document.getElementById('sharedWeirdBox');
  function setGameMode(mode){const friend=mode==='friend';friendModePanel.classList.toggle('hidden',!friend);computerModePanel.classList.toggle('hidden',friend);sharedWeirdBox.classList.remove('hidden');playFriendMode.classList.toggle('active',friend);playComputerMode.classList.toggle('active',!friend)}
  function openGameMode(){friendModePanel.classList.add('hidden');computerModePanel.classList.add('hidden');sharedWeirdBox.classList.add('hidden');sharedWeirdBox.querySelectorAll('input').forEach(x=>x.checked=false);playFriendMode.classList.remove('active');playComputerMode.classList.remove('active');gameModeBox.classList.remove('hidden')}
  document.getElementById('newGameDash').onclick=openGameMode;
  closeGameMode.onclick=()=>gameModeBox.classList.add('hidden');
  gameModeBox.addEventListener('click',e=>{if(e.target===gameModeBox)gameModeBox.classList.add('hidden')});
  playFriendMode.onclick=()=>setGameMode('friend');
  playComputerMode.onclick=()=>setGameMode('computer');
  startFriendGame.onclick=async()=>{startFriendGame.disabled=true;try{await createGame();gameModeBox.classList.add('hidden');}finally{startFriendGame.disabled=false}};
  gameModeBox.querySelectorAll('[data-cpu-difficulty]').forEach(btn=>btn.onclick=()=>createComputerGame(btn.dataset.cpuDifficulty));'''
if old_handlers in js:
    js = js.replace(old_handlers,new_handlers,1)
elif "const playComputerMode=document.getElementById('playComputerMode')" not in js:
    # Some packaged bundles are minified differently. Inject an equivalent
    # delegated controller rather than failing the whole release.
    fallback = '''\n<script id="scrobble-approved-new-game-controller">\n(()=>{\n const box=document.getElementById('gameModeBox'); if(!box)return;\n const friend=document.getElementById('playFriendMode'),computer=document.getElementById('playComputerMode');\n const fp=document.getElementById('friendModePanel'),cp=document.getElementById('computerModePanel'),weird=document.getElementById('sharedWeirdBox');\n const choose=(mode)=>{const f=mode==='friend';fp?.classList.toggle('hidden',!f);cp?.classList.toggle('hidden',f);weird?.classList.remove('hidden');friend?.classList.toggle('active',f);computer?.classList.toggle('active',!f)};\n friend?.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();choose('friend')},true);\n computer?.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();choose('computer')},true);\n})();\n</script>\n'''
    page=index.read_text()
    page=page.replace('</body>',fallback+'</body>',1)
    index.write_text(page)
app.write_text(js)

# Startup masking intentionally removed after 1.0.11-1.0.13 WKWebView regressions.
# Native iOS launch-screen work will address the cosmetic pre-splash flash separately.

# Replace the packaged unauthenticated account form itself. This runs before the
# onboarding overlay is injected, so Login/Create no longer fight the legacy
# combined form or its profile-photo controls.
text = index.read_text()
old_account = '<div id="accountState" class="accountState"></div><div id="passwordAccountForm" class="passwordAccountForm"><label class="accountLabel" for="accountUsername">USERNAME <span style="font-weight:500">(NEW ACCOUNTS)</span></label><input id="accountUsername" class="accountInput" type="text" autocomplete="nickname" autocapitalize="none" spellcheck="false" maxlength="20" placeholder="Choose your player name"><div class="usernameHint">3–20 letters, numbers, or underscores. This is what other players will see.</div><label class="accountLabel" for="accountEmail">EMAIL</label><input id="accountEmail" class="accountInput" type="email" autocomplete="email" autocapitalize="none" spellcheck="false" placeholder="you@example.com"><label class="accountLabel" for="accountPassword">PASSWORD</label><input id="accountPassword" class="accountInput" type="password" autocomplete="current-password" placeholder="At least 6 characters"><button id="signInAccount" class="accountPrimary" type="button">SIGN IN</button><button id="createAccount" class="accountSecondary" type="button">CREATE ACCOUNT</button><button id="forgotPassword" class="accountLink" type="button">Forgot password?</button></div>'
new_account = '<div id="accountState" class="accountState"></div><div id="passwordAccountForm" class="passwordAccountForm"><div id="loginAccountPanel" class="scrobbleAuthPanel hidden"><label class="accountLabel" for="accountEmail">EMAIL</label><input id="accountEmail" class="accountInput" type="email" autocomplete="email" autocapitalize="none" spellcheck="false" placeholder="you@example.com"><label class="accountLabel" for="accountPassword">PASSWORD</label><input id="accountPassword" class="accountInput" type="password" autocomplete="current-password" placeholder="At least 6 characters"><button id="signInAccount" class="accountPrimary" type="button">SIGN IN</button><button id="forgotPassword" class="accountLink" type="button">Forgot password?</button></div><div id="createAccountPanel" class="scrobbleAuthPanel hidden"><label class="accountLabel" for="accountUsername">USERNAME</label><input id="accountUsername" class="accountInput" type="text" autocomplete="nickname" autocapitalize="none" spellcheck="false" maxlength="20" placeholder="Choose your player name"><div class="usernameHint">3–20 letters, numbers, or underscores. This is what other players will see.</div><label class="accountLabel" for="accountCreateEmail">EMAIL</label><input id="accountCreateEmail" class="accountInput" type="email" autocomplete="email" autocapitalize="none" spellcheck="false" placeholder="you@example.com"><label class="accountLabel" for="accountCreatePassword">PASSWORD</label><input id="accountCreatePassword" class="accountInput" type="password" autocomplete="new-password" placeholder="At least 6 characters"><button id="createAccount" class="accountPrimary" type="button">CREATE ACCOUNT</button></div></div>'
if old_account not in text:
    raise SystemExit('Exact packaged account form not found; refusing partial onboarding patch')
text = text.replace(old_account,new_account,1)
index.write_text(text)

app = Path('www/app-v3140.js')
js = app.read_text()
needle = "const accountBox=document.getElementById('accountBox'),accountDash=document.getElementById('accountDash'),closeAccount=document.getElementById('closeAccount'),accountIdentity=document.getElementById('accountIdentity'),accountState=document.getElementById('accountState'),passwordAccountForm=document.getElementById('passwordAccountForm'),accountUsername=document.getElementById('accountUsername'),accountEmail=document.getElementById('accountEmail'),accountPassword=document.getElementById('accountPassword'),signInAccount=document.getElementById('signInAccount'),createAccount=document.getElementById('createAccount'),forgotPassword=document.getElementById('forgotPassword'),"
if needle not in js:
    raise SystemExit('Exact packaged account JS controls not found')
js = js.replace(needle,needle+"loginAccountPanel=document.getElementById('loginAccountPanel'),createAccountPanel=document.getElementById('createAccountPanel'),accountCreateEmail=document.getElementById('accountCreateEmail'),accountCreatePassword=document.getElementById('accountCreatePassword'),",1)
js = js.replace("function authCredentials(){\\n    const email=accountEmail.value.trim().toLowerCase();\\n    const password=accountPassword.value;","function authCredentials(create=false){\\n    const email=(create?accountCreateEmail:accountEmail).value.trim().toLowerCase();\\n    const password=(create?accountCreatePassword:accountPassword).value;",1)
js = js.replace("createAccount.onclick=async()=>{\\n    const username=newAccountUsername();if(!username)return;\\n    const credentials=authCredentials();if(!credentials)return;","createAccount.onclick=async()=>{\\n    const username=newAccountUsername();if(!username)return;\\n    const credentials=authCredentials(true);if(!credentials)return;",1)
app.write_text(js)

# Next-release onboarding. Use the game's blue visual language and drive the
# existing account form explicitly instead of relying on its previous mode.
onboarding = r'''
<style id="scrobble-onboarding-v3-style">
#scrobbleOnboardingV2{position:fixed;inset:0;z-index:2147483000;background:linear-gradient(180deg,#1699dc 0%,#0877bb 58%,#064b82 100%);display:flex;align-items:center;justify-content:center;padding:calc(env(safe-area-inset-top) + 22px) 22px calc(env(safe-area-inset-bottom) + 22px);font-family:Arial,Helvetica,sans-serif}
#scrobbleOnboardingV2.hidden{display:none!important}
#scrobbleOnboardingV2 .obCard{width:min(100%,430px);background:linear-gradient(180deg,#0e83c7,#0867a5);border:2px solid rgba(255,255,255,.22);border-radius:28px;padding:34px 26px 28px;box-shadow:0 24px 70px rgba(0,0,0,.25);text-align:center}
#scrobbleOnboardingV2 h1{margin:0 0 10px;color:#fff;font-size:36px;line-height:1.04}
#scrobbleOnboardingV2 p{margin:0 0 28px;color:#d9f1ff;font-size:18px;line-height:1.35}
#scrobbleOnboardingV2 .obActions{display:flex;gap:12px}
#scrobbleOnboardingV2 button{flex:1;min-height:58px;border-radius:14px;border:2px solid #fff;background:transparent;color:#fff;font-size:16px;font-weight:900;padding:10px}
#scrobbleOnboardingV2 button.primary{background:#f2bd45;border-color:#f2bd45;color:#173044}
@media(max-width:360px){#scrobbleOnboardingV2 .obActions{flex-direction:column}}

/* Account sheet: same family as Welcome, with no mystery profile/photo blocks. */
#accountBox{background:linear-gradient(180deg,#1699dc 0%,#0877bb 58%,#064b82 100%)!important}
#accountBox>div{background:linear-gradient(180deg,#0e83c7,#0867a5)!important;border:2px solid rgba(255,255,255,.22)!important;color:#fff!important}
#accountBox h1,#accountBox h2,#accountBox h3,#accountBox .accountLabel,#accountBox label,#accountBox .usernameHint{color:#fff!important}\n#accountBox .accountState:empty{display:none!important}\n#accountBox .passwordAccountForm{background:transparent!important}
#accountBox input{background:#fff!important;color:#173044!important}
#accountBox .scrobbleAuthHide,#accountBox .scrobbleAuthPanel.hidden{display:none!important}\n#accountBox .accountIdentity:has(+ .accountState){display:none!important}
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
<script id="scrobble-onboarding-v3-script">
(()=>{
  const overlay=document.getElementById('scrobbleOnboardingV2');
  const account=document.getElementById('accountBox');
  if(!overlay||!account) return;
  const createBtn=document.getElementById('scrobbleCreateChoice');
  const loginBtn=document.getElementById('scrobbleLoginChoice');
  const signIn=document.getElementById('signInAccount');
  const create=document.getElementById('createAccount');
  const username=document.getElementById('accountUsername');
  const forgot=document.getElementById('forgotPassword');

  const signedIn=()=>{
    const logout=document.getElementById('logoutAccount');
    return !!logout && !logout.classList.contains('hidden');
  };
  const setHeading=(mode)=>{
    const heading=[...account.querySelectorAll('h1,h2,h3')].find(el=>/SCROBBLE|ACCOUNT|SIGN/i.test(el.textContent||''));
    if(heading) heading.textContent=mode==='login'?'Welcome Back!':'Create Your Scrobble Account';
  };
  const hideCreateExtras=(hide)=>{
    if(username){
      const wrap=username.closest('label')||username.parentElement;
      if(wrap) wrap.classList.toggle('scrobbleAuthHide',hide);
      const hint=[...account.querySelectorAll('*')].find(el=>/3.?20 letters/i.test(el.textContent||''));
      if(hint) hint.classList.toggle('scrobbleAuthHide',hide);
    }
  };
  const setProfileChrome=(show)=>{
    const identity=document.getElementById('accountIdentity');
    if(identity){
      identity.classList.toggle('scrobbleAuthHide',!show);
      identity.style.removeProperty('display');
    }
    account.querySelectorAll('input[type="file"],img').forEach(el=>{
      const wrap=el.closest('button,label,div')||el;
      wrap.classList.toggle('scrobbleAuthHide',!show);
    });
    [...account.querySelectorAll('button,div')].forEach(el=>{
      const t=(el.textContent||'').trim();
      if(/^(UPLOAD PHOTO|ADD PHOTO|EDIT PHOTO|CHANGE PHOTO|REMOVE|REMOVE PHOTO|TAKE PHOTO|CHOOSE PHOTO|PROFILE PHOTO)$/i.test(t)){
        el.classList.toggle('scrobbleAuthHide',!show);
      }
    });
  };
  const showAccount=(mode)=>{
    overlay.classList.add('hidden');
    account.classList.remove('hidden');
    setHeading(mode);
    const login=mode==='login';
    account.classList.toggle('scrobbleLoginMode',login);
    account.classList.toggle('scrobbleCreateMode',!login);
    setProfileChrome(!login);
    const loginPanel=document.getElementById('loginAccountPanel');
    const createPanel=document.getElementById('createAccountPanel');
    const enforce=()=>{
      loginPanel?.classList.toggle('hidden',!login);
      createPanel?.classList.toggle('hidden',login);
      account.classList.toggle('scrobbleLoginMode',login);
      account.classList.toggle('scrobbleCreateMode',!login);
      setProfileChrome(!login);
    };
    enforce();
    // The packaged renderAccount routine can run asynchronously after this click.
    // Reassert the selected auth panel for a short window so it cannot reveal both.
    [0,50,150,350,750].forEach(ms=>setTimeout(enforce,ms));
    // Clear stale values so one auth path never inherits the other path's state.
    account.querySelectorAll('input[type="email"],input[type="password"]').forEach(el=>el.value='');
  };
  createBtn.onclick=()=>showAccount('create');
  loginBtn.onclick=()=>showAccount('login');

  // On first-run authentication, X means Back to Welcome, not dismiss the
  // required login gate and reveal an unusable unauthenticated Games screen.
  const close=document.getElementById('closeAccount');
  if(close){
    close.addEventListener('click',e=>{
      if(signedIn()) return; // Preserve the normal Account-sheet close behavior.
      e.preventDefault();
      e.stopImmediatePropagation();
      account.classList.add('hidden');
      overlay.classList.remove('hidden');
    },true);
  }
  // The packaged account description has its own legacy gray color rule.
  // Style the exact explanatory line, not just generic paragraph selectors.
  [...account.querySelectorAll('p,div,span')].forEach(el=>{
    if(el.children.length===0 && /Create an account or sign in to keep your games/i.test(el.textContent||'')){
      el.style.setProperty('color','#e9f7ff','important');
    }
  });

  let checks=0;
  const decide=()=>{
    if(signedIn()){overlay.classList.add('hidden');return}
    if(++checks<12){setTimeout(decide,125);return}
    if(!new URLSearchParams(location.search).get('join')) overlay.classList.remove('hidden');
  };
  decide();
})();
</script>
'''
text = index.read_text()
# Remove prior onboarding if present, then insert v3 once.
text = re.sub(r'<style id="scrobble-onboarding-v2-style">.*?</script>\s*', '', text, flags=re.S)
if 'id="scrobbleOnboardingV2"' not in text:
    text = text.replace('</body>', onboarding + '</body>')
index.write_text(text)


# FINAL auth DOM pass. Legacy profile controls are siblings in accountBox rather
# than a reliably shaped accountIdentity wrapper. Remove them by their actual IDs
# and controls, without assuming one HTML nesting pattern.
text = index.read_text()
# Preserve the original profile DOM and all its IDs: app-v3140.js binds photo
# handlers during bootstrap even when onboarding hides the profile UI. Removing
# the children (or replacing them with an empty node) crashes initialization,
# leaving both Sign In and Forgot Password inert. Hide it with CSS only.
# The current packaged app can expose profile controls independently. Hide/remove
# them at runtime by stable control IDs/classes instead of brittle markup matching.
final_auth_css = '''
<style id="scrobble-final-auth-layout">
#accountBox{background:linear-gradient(180deg,#1699dc 0%,#0877bb 58%,#064b82 100%)!important}
#accountBox .accountCard,#accountBox .modalCard,#accountBox>div{background:#0b75b6!important;color:#fff!important}
#accountBox .scrobbleAuthPanel{display:block!important}
#accountBox .scrobbleAuthPanel.hidden{display:none!important}
#accountBox .accountState:empty{display:none!important}
#accountBox .accountLabel,#accountBox .usernameHint{color:#fff!important}
#accountBox .accountInput{background:#fff!important;color:#173044!important}
#accountBox .accountSub,#accountBox .accountSubtitle,#accountBox p{color:#e9f7ff!important}
#accountBox .accountPrimary{background:#f2bd45!important;color:#173044!important;border-color:#f2bd45!important}
#accountBox .accountLink{color:#fff!important}
#accountBox #accountIdentity{display:block!important}\n#accountBox.scrobbleLoginMode #accountIdentity{display:none!important}\n#accountBox.scrobbleCreateMode #accountIdentity{display:block!important}\n#accountBox #closeAccount{display:flex!important;visibility:visible!important;opacity:1!important;pointer-events:auto!important}
</style>
<script id="scrobble-final-auth-cleanup">
(()=>{
 const box=document.getElementById('accountBox'); if(!box)return;
 const clean=()=>{
   const hideProfile=box.classList.contains('scrobbleLoginMode');
   box.querySelectorAll('input[type="file"]').forEach(el=>{
     const wrap=el.closest('div')||el;
     if(hideProfile) wrap.style.setProperty('display','none','important');
     else wrap.style.removeProperty('display');
   });
   box.querySelectorAll('button').forEach(el=>{
     if(/UPLOAD PHOTO|ADD PHOTO|EDIT PHOTO|CHANGE PHOTO|REMOVE PHOTO|TAKE PHOTO|CHOOSE PHOTO/i.test(el.textContent||'')){
       const wrap=el.closest('div')||el;
       if(hideProfile) wrap.style.setProperty('display','none','important');
       else wrap.style.removeProperty('display');
     }
   });
 };
 clean(); new MutationObserver(clean).observe(box,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
})();
</script>
'''
if 'id="scrobble-final-auth-layout"' not in text:
    text = text.replace('</head>', final_auth_css + '</head>', 1)
index.write_text(text)

# New-game activity isolation. The activity banner is transient game state; a fresh
# game must never inherit the previous game's last-move message.
activity_fix = r'''
<script id="scrobble-new-game-activity-reset">
(()=>{
  let armedUntil=0;
  const isNewGameAction=(el)=>{
    const t=(el?.textContent||'').trim();
    return /PLAY (THE )?COMPUTER|PLAY (A )?FRIEND|NEW GAME|REMATCH/i.test(t);
  };
  const clearStale=()=>{
    if(Date.now()>armedUntil) return;
    document.querySelectorAll('div,span,p').forEach(el=>{
      if(el.children.length) return;
      const t=(el.textContent||'').trim();
      if(/^[^\\n]{1,40} played .+ for \\d+$/i.test(t)) el.textContent='';
    });
  };
  document.addEventListener('click',e=>{
    const control=e.target.closest?.('button,a,[role="button"]');
    if(!isNewGameAction(control)) return;
    armedUntil=Date.now()+1500;
    clearStale();
    setTimeout(clearStale,50);
    setTimeout(clearStale,250);
    setTimeout(clearStale,700);
    setTimeout(clearStale,1400);
  },true);
})();
</script>
'''
text = index.read_text()
if 'id="scrobble-new-game-activity-reset"' not in text:
    text = text.replace('</body>', activity_fix + '</body>', 1)
index.write_text(text)

final_index = index.read_text()
assert final_index.count('id="playComputerMode"') == 1, "Approved Play Computer chooser missing"
assert final_index.count('id="startFriendGame"') == 1, "Approved Share Invite action missing"
assert final_index.count('id="sharedWeirdBox"') == 1, "Make It Weird missing or duplicated"
assert 'OR PLAY THE COMPUTER' not in final_index, "Legacy giant New Game layout survived"
assert ("playFriendMode.onclick=()=>setGameMode('friend')" in app.read_text() or 'id="scrobble-approved-new-game-controller"' in final_index), "Friend chooser handler regression"
assert ("playComputerMode.onclick=()=>setGameMode('computer')" in app.read_text() or 'id="scrobble-approved-new-game-controller"' in final_index), "Computer chooser handler regression"
assert final_index.count('id="accountIdentity"') == 1, "Original account identity DOM missing"
assert '#accountBox #accountIdentity{display:block!important}' in final_index, "Signed-in profile photo UI hidden"
assert final_index.count('id="loginAccountPanel"') == 1, "Login panel missing or duplicated"
assert final_index.count('id="createAccountPanel"') == 1, "Create panel missing or duplicated"
assert 'PATCH_20260930_FINAL' in final_index, "Final patch marker missing"
assert "account.classList.toggle('scrobbleCreateMode',!login)" in final_index, "Create mode class wiring missing"
assert "setProfileChrome(!login)" in final_index, "Create photo controls wiring missing"
assert "Welcome Back!" in final_index, "Login heading regression"
assert final_index.index('id="sharedWeirdBox"') < final_index.index('id="computerModePanel"'), "Make It Weird must precede computer difficulty"
assert "startFriendGame.onclick=async()=>{" in app.read_text(), "Friend share action wiring missing"
assert "await createGame();gameModeBox.classList.add('hidden')" in app.read_text(), "Friend create/share flow missing"
assert "const share=[...document.querySelectorAll" not in app.read_text(), "Recursive share-button heuristic returned"
assert 'id="scrobble-haptics"' in final_index, "Haptics bridge missing"


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

# Final regression checks must run AFTER all native invite/share/deep-link
# scripts have been injected. Earlier placement falsely failed every build.
app_source = app.read_text()
index_source = index.read_text()
assert "https://yayeverybody.com/?join=" in app_source, "Public invite URL regression"
assert "capacitor://localhost/?join=" not in app_source, "Native localhost invite URL regression"
assert "location.replace(next)" in index_source, "Universal Link clean-bootstrap missing"
assert "script.src='app-v3140.js?nativejoin='" not in index_source, "Unsafe live script re-bootstrap returned"
assert "appUrlOpen" in index_source, "Warm-app Universal Link listener missing"
assert "getLaunchUrl" in index_source, "Cold-launch Universal Link handling missing"
assert 'id="scrobble-ios-native-share"' in index_source, "Native share bridge missing"
assert 'id="loginAccountPanel"' in index_source and 'id="createAccountPanel"' in index_source, "Separate auth panels missing"
assert 'USERNAME <span style="font-weight:500">(NEW ACCOUNTS)</span>' not in index_source, "Legacy combined auth form survived"
assert 'scrobbleAuthPanel hidden' in index_source, "Auth panels must default hidden"
assert 'scrobble-prepaint-guard' not in index_source, "Unsafe custom startup guard returned"
assert 'scrobbleStartupSplash' not in index_source, "Unsafe custom web splash returned"