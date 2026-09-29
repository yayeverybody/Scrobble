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


# Scrobble 1.0.1 UI cleanup: use the real packaged controls.
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
if old_game not in text:
    raise SystemExit('New Game source block not found')
text = text.replace(old_game,new_game,1)

old_account = '<div id="accountState" class="accountState"></div><div id="passwordAccountForm" class="passwordAccountForm"><label class="accountLabel" for="accountUsername">USERNAME <span style="font-weight:500">(NEW ACCOUNTS)</span></label><input id="accountUsername" class="accountInput" type="text" autocomplete="nickname" autocapitalize="none" spellcheck="false" maxlength="20" placeholder="Choose your player name"><div class="usernameHint">3–20 letters, numbers, or underscores. This is what other players will see.</div><label class="accountLabel" for="accountEmail">EMAIL</label><input id="accountEmail" class="accountInput" type="email" autocomplete="email" autocapitalize="none" spellcheck="false" placeholder="you@example.com"><label class="accountLabel" for="accountPassword">PASSWORD</label><input id="accountPassword" class="accountInput" type="password" autocomplete="current-password" placeholder="At least 6 characters"><button id="signInAccount" class="accountPrimary" type="button">SIGN IN</button><button id="createAccount" class="accountSecondary" type="button">CREATE ACCOUNT</button><button id="forgotPassword" class="accountLink" type="button">Forgot password?</button></div>'
new_account = '<div id="accountState" class="accountState"></div><div id="passwordAccountForm" class="passwordAccountForm"><div class="accountModeChooser"><button id="showLoginAccount" class="accountModeChoice" type="button">LOGIN</button><button id="showCreateAccount" class="accountModeChoice" type="button">CREATE AN ACCOUNT</button></div><div id="loginAccountPanel" class="accountModePanel hidden"><label class="accountLabel" for="accountEmail">EMAIL</label><input id="accountEmail" class="accountInput" type="email" autocomplete="email" autocapitalize="none" spellcheck="false" placeholder="you@example.com"><label class="accountLabel" for="accountPassword">PASSWORD</label><input id="accountPassword" class="accountInput" type="password" autocomplete="current-password" placeholder="At least 6 characters"><button id="signInAccount" class="accountPrimary" type="button">SIGN IN</button><button id="forgotPassword" class="accountLink" type="button">Forgot password?</button></div><div id="createAccountPanel" class="accountModePanel hidden"><label class="accountLabel" for="accountUsername">USERNAME</label><input id="accountUsername" class="accountInput" type="text" autocomplete="nickname" autocapitalize="none" spellcheck="false" maxlength="20" placeholder="Choose your player name"><div class="usernameHint">3–20 letters, numbers, or underscores. This is what other players will see.</div><label class="accountLabel" for="accountCreateEmail">EMAIL</label><input id="accountCreateEmail" class="accountInput" type="email" autocomplete="email" autocapitalize="none" spellcheck="false" placeholder="you@example.com"><label class="accountLabel" for="accountCreatePassword">PASSWORD</label><input id="accountCreatePassword" class="accountInput" type="password" autocomplete="new-password" placeholder="At least 6 characters"><button id="createAccount" class="accountPrimary" type="button">CREATE ACCOUNT</button></div></div>'
if old_account not in text:
    raise SystemExit('Account source block not found')
text = text.replace(old_account,new_account,1)

flow_style = '''
<style id="scrobble-native-flow-cleanup">
#gameModeBox .modeChooser,#accountBox .accountModeChooser{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}
#gameModeBox .modeChoice,#accountBox .accountModeChoice{min-height:48px;border:2px solid #0d80cd;border-radius:12px;background:#fff;color:#0d80cd;font-weight:900}
#gameModeBox .modeChoice.active,#accountBox .accountModeChoice.active{background:#0d80cd;color:#fff}
#gameModeBox .modePanel.hidden,#accountBox .accountModePanel.hidden{display:none!important}
#gameModeBox .friendStart{width:100%;min-height:48px;margin-top:12px;border:0;border-radius:12px;background:#0d80cd;color:#fff;font-weight:900}
</style>
'''
text = text.replace('</head>',flow_style+'</head>',1)
index.write_text(text)

app = Path('www/app-v3140.js')
js = app.read_text()
js = js.replace("function inviteURL(code){return location.origin+location.pathname+'?join='+encodeURIComponent(code)}", "function inviteURL(code){return 'https://yayeverybody.com/?join='+encodeURIComponent(code)}",1)

needle = "const accountBox=document.getElementById('accountBox'),accountDash=document.getElementById('accountDash'),closeAccount=document.getElementById('closeAccount'),accountIdentity=document.getElementById('accountIdentity'),accountState=document.getElementById('accountState'),passwordAccountForm=document.getElementById('passwordAccountForm'),accountUsername=document.getElementById('accountUsername'),accountEmail=document.getElementById('accountEmail'),accountPassword=document.getElementById('accountPassword'),signInAccount=document.getElementById('signInAccount'),createAccount=document.getElementById('createAccount'),forgotPassword=document.getElementById('forgotPassword'),"
if needle not in js:
    raise SystemExit('Account JS controls not found')
js = js.replace(needle,needle+"showLoginAccount=document.getElementById('showLoginAccount'),showCreateAccount=document.getElementById('showCreateAccount'),loginAccountPanel=document.getElementById('loginAccountPanel'),createAccountPanel=document.getElementById('createAccountPanel'),accountCreateEmail=document.getElementById('accountCreateEmail'),accountCreatePassword=document.getElementById('accountCreatePassword'),",1)

render = '  function renderAccount(){\n'
account_modes = "  function setAccountMode(mode){const login=mode==='login';loginAccountPanel.classList.toggle('hidden',!login);createAccountPanel.classList.toggle('hidden',login);showLoginAccount.classList.toggle('active',login);showCreateAccount.classList.toggle('active',!login)}\n  showLoginAccount.onclick=()=>setAccountMode('login');showCreateAccount.onclick=()=>setAccountMode('create');\n"
js = js.replace(render,account_modes+render,1)
js = js.replace("passwordAccountForm.classList.remove('hidden');\n      passwordSetupToggle.classList.add('hidden');","passwordAccountForm.classList.remove('hidden');loginAccountPanel.classList.add('hidden');createAccountPanel.classList.add('hidden');showLoginAccount.classList.remove('active');showCreateAccount.classList.remove('active');\n      passwordSetupToggle.classList.add('hidden');",1)
js = js.replace("function authCredentials(){\n    const email=accountEmail.value.trim().toLowerCase();\n    const password=accountPassword.value;","function authCredentials(create=false){\n    const email=(create?accountCreateEmail:accountEmail).value.trim().toLowerCase();\n    const password=(create?accountCreatePassword:accountPassword).value;",1)
js = js.replace("createAccount.onclick=async()=>{\n    const username=newAccountUsername();if(!username)return;\n    const credentials=authCredentials();if(!credentials)return;","createAccount.onclick=async()=>{\n    const username=newAccountUsername();if(!username)return;\n    const credentials=authCredentials(true);if(!credentials)return;",1)

old_handlers = "  document.getElementById('newGameDash').onclick=()=>gameModeBox.classList.remove('hidden');\n  closeGameMode.onclick=()=>gameModeBox.classList.add('hidden');\n  gameModeBox.addEventListener('click',e=>{if(e.target===gameModeBox)gameModeBox.classList.add('hidden')});\n  playFriendMode.onclick=()=>{gameModeBox.classList.add('hidden');createGame()};\n  gameModeBox.querySelectorAll('[data-cpu-difficulty]').forEach(btn=>btn.onclick=()=>createComputerGame(btn.dataset.cpuDifficulty));"
new_handlers = "  const playComputerMode=document.getElementById('playComputerMode'),friendModePanel=document.getElementById('friendModePanel'),computerModePanel=document.getElementById('computerModePanel'),startFriendGame=document.getElementById('startFriendGame');\n  function setGameMode(mode){const friend=mode==='friend';friendModePanel.classList.toggle('hidden',!friend);computerModePanel.classList.toggle('hidden',friend);playFriendMode.classList.toggle('active',friend);playComputerMode.classList.toggle('active',!friend)}\n  function openGameMode(){friendModePanel.classList.add('hidden');computerModePanel.classList.add('hidden');playFriendMode.classList.remove('active');playComputerMode.classList.remove('active');gameModeBox.classList.remove('hidden')}\n  document.getElementById('newGameDash').onclick=openGameMode;\n  closeGameMode.onclick=()=>gameModeBox.classList.add('hidden');\n  gameModeBox.addEventListener('click',e=>{if(e.target===gameModeBox)gameModeBox.classList.add('hidden')});\n  playFriendMode.onclick=()=>setGameMode('friend');playComputerMode.onclick=()=>setGameMode('computer');startFriendGame.onclick=()=>{gameModeBox.classList.add('hidden');createGame()};\n  gameModeBox.querySelectorAll('[data-cpu-difficulty]').forEach(btn=>btn.onclick=()=>createComputerGame(btn.dataset.cpuDifficulty));"
if old_handlers not in js:
    raise SystemExit('New Game JS handlers not found')
js = js.replace(old_handlers,new_handlers,1)
app.write_text(js)


# Universal Links: open https://yayeverybody.com/?join=... directly in Yay Everybody.
# Capacitor delivers universal links through App.addListener('appUrlOpen', ...).
app = Path('www/app-v3140.js')
js = app.read_text()
universal_link_handler = """
;(()=>{
  function consumeInviteUrl(raw){
    try{
      const u=new URL(raw);
      if(u.hostname!=='yayeverybody.com' && u.hostname!=='www.yayeverybody.com')return;
      const code=u.searchParams.get('join');
      if(!code)return;
      const target=location.pathname+'?join='+encodeURIComponent(code);
      history.replaceState(null,'',target);
      location.reload();
    }catch(e){console.error('Invite link error',e)}
  }
  const cap=window.Capacitor;
  const App=cap&&cap.Plugins&&cap.Plugins.App;
  if(App&&App.addListener)App.addListener('appUrlOpen',({url})=>consumeInviteUrl(url));
})();
"""
if "App.addListener('appUrlOpen'" not in js:
    js += universal_link_handler
app.write_text(js)
