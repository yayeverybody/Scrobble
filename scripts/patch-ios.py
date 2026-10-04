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

# Extend the existing notification UI with native registration and nudges.
app=Path('www/app-v3140.js');js=app.read_text()
marker='  function notificationSetupCopy(){'
if js.count(marker)!=1: raise SystemExit('Notification setup function not found')
native_source=Path(__file__).with_name('native-notifications.js').read_text()
js=js.replace(marker,native_source+'\n'+marker,1)
js=js.replace('  async function ensurePushSubscription(requestPermission=false){', '  async function ensurePushSubscription(requestPermission=false){\n    if(nativePush())return registerNativeTurnNotifications(requestPermission);',1)
js=js.replace(marker,marker+"\n    if(nativePush())return{copy:'Get a notification when it’s your turn or a friend nudges you.',help:'',action:'TURN ON NOTIFICATIONS'};",1)
js=js.replace('  async function maybeShowPushPrompt(){', "  async function maybeShowPushPrompt(){\n    if(nativePush()&&user){\n      try{if(await registerNativeTurnNotifications(false))return}catch(e){console.warn('Native notification registration failed',e)}\n      openNotificationSetup(false);return;\n    }",1)
js=js.replace('    if(isIOS()&&!isStandalone()){', '    if(!nativePush()&&isIOS()&&!isStandalone()){',1)
js=js.replace('  logoutAccount.onclick=async()=>{', '  logoutAccount.onclick=async()=>{\n    try{await stopNativeTurnNotifications()}catch(e){console.warn(\'Could not unregister notifications\',e)}',1)
card_marker="        end.onclick=e=>{e.stopPropagation();askEndGame(g.id)};\n        wrap.append(card,end);active.appendChild(wrap)"
card_new="""        end.onclick=e=>{e.stopPropagation();askEndGame(g.id)};
        wrap.classList.add('friendGameCard');
        card.querySelector('.gameChevron')?.remove();
        const actions=document.createElement('div');actions.className='gameCardActions';
        const open=document.createElement('button');open.type='button';open.className='openGameBtn';
        open.textContent=waiting?'SHARE INVITE':review?'REVIEW WORD':'OPEN GAME';
        open.setAttribute('aria-label',waiting?'Share game invite':'Open game with '+names.opponent);
        open.onclick=e=>{e.stopPropagation();card.onclick()};actions.appendChild(open);
        wrap.append(card,end,actions);
        if(!waiting&&!mine){
          const nudge=document.createElement('button');nudge.type='button';nudge.className='nudgeGameBtn';nudge.textContent='NUDGE';
          nudge.setAttribute('aria-label','Nudge '+names.opponent);
          nudge.onclick=e=>{e.stopPropagation();void nudgeGame(g.id,nudge)};
          actions.appendChild(nudge);
        }
        active.appendChild(wrap)"""
if js.count(card_marker)!=1: raise SystemExit('Opponent game card insertion target not found')
js=js.replace(card_marker,card_new,1);app.write_text(js)
text=index.read_text()
card_style='''
<style id="scrobble-nudge-style">
#scrobble-dashboard .friendGameCard{border:1px solid rgba(97,183,235,.55);border-radius:22px;overflow:hidden;background:linear-gradient(120deg,#0d5896,#073769);box-shadow:0 8px 20px rgba(0,0,0,.14)}
#scrobble-dashboard .friendGameCard .gameCard{border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;padding:16px 42px 14px 14px!important;min-height:96px!important;gap:10px!important}
#scrobble-dashboard .friendGameCard .gameIdentity{gap:10px!important}
#scrobble-dashboard .friendGameCard .oppAvatar{width:48px!important;height:48px!important;min-width:48px!important;flex:0 0 48px!important}
#scrobble-dashboard .friendGameCard .opponent{font-size:17px!important;white-space:normal!important;overflow-wrap:anywhere;text-overflow:clip!important}
#scrobble-dashboard .friendGameCard .gameMeta{font-size:12px!important;line-height:1.4!important}
#scrobble-dashboard .friendGameCard .gameScores{min-width:76px!important;gap:6px!important}
#scrobble-dashboard .friendGameCard .scoreSide strong{font-size:25px!important}
#scrobble-dashboard .friendGameCard .endGameBtn{top:10px!important;right:10px!important;transform:none!important}
#scrobble-dashboard .gameCardActions{display:flex;gap:10px;padding:12px 14px;border-top:1px solid rgba(154,211,247,.2);background:rgba(0,22,49,.18)}
#scrobble-dashboard .gameCardActions button{flex:1;min-width:0;min-height:44px;padding:9px 10px;border-radius:12px;font-size:13px;font-weight:900;letter-spacing:.3px;cursor:pointer}
#scrobble-dashboard .openGameBtn{border:1px solid #72c3f5;background:#1269a7;color:#fff}
#scrobble-dashboard .nudgeGameBtn{border:0;background:#f2bd45;color:#173044}
#scrobble-dashboard .nudgeGameBtn:disabled{opacity:.65}
#scrobble-dashboard .gameCardActions button:focus-visible{outline:3px solid #fff;outline-offset:2px}
</style>
'''
text=text.replace('</head>',card_style+'</head>',1)
index.write_text(text)

import json
config=Path('capacitor.config.json');settings=json.loads(config.read_text())
settings.setdefault('plugins',{})['PushNotifications']={'presentationOptions':['badge','sound','banner','list']}
config.write_text(json.dumps(settings,indent=2)+'\n')

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
    "  const duration=3000;": "  const duration=2000;",
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

# Precise tile feedback occurs only after a valid drop/placement changes the board.
game=engine.read_text()
old="selected=null;render();pinch=null;panGesture=null;setTimeout(()=>focusCell(r,c),50)"
assert game.count(old)==1, 'Tap-placement feedback anchor missing'
game=game.replace(old,"selected=null;render();window.ScrobbleHaptics?.tile?.();pinch=null;panGesture=null;setTimeout(()=>focusCell(r,c),50)",1)
old="racks[current].push(old.letter)}}selected=null;render();if(placed){"
assert game.count(old)==1, 'Rack-return feedback anchor missing'
game=game.replace(old,"racks[current].push(old.letter);window.ScrobbleHaptics?.tileReturn?.()}}selected=null;render();if(placed){window.ScrobbleHaptics?.tile?.();",1)
for old,new in {
    "if(err){status.textContent=err;return}": "if(err){window.ScrobbleHaptics?.error?.();status.textContent=err;return}",
    "if(!words?.length){status.textContent='That does not make a word.';return}": "if(!words?.length){window.ScrobbleHaptics?.error?.();status.textContent='That does not make a word.';return}",
    "showComputerRejection(attemptedWords,badWord.word);": "window.ScrobbleHaptics?.error?.();showComputerRejection(attemptedWords,badWord.word);",
}.items():
    assert game.count(old)==1, 'Rejected-move feedback anchor missing'
    game=game.replace(old,new,1)
engine.write_text(game)

# Independent, persistent sound and haptic preferences in the existing account panel.
text=index.read_text()
anchor='<button id="logoutAccount"'
assert text.count(anchor)==1, 'Feedback settings account anchor missing'
controls='<div id="feedbackSettings" style="margin:16px 0;padding:14px;border:1px solid #72c3f5;border-radius:12px;color:#fff;background:#0b477a"><div style="font-weight:900;margin-bottom:8px">GAME FEEDBACK</div><label style="display:flex;align-items:center;gap:10px;min-height:44px;color:#fff"><input id="feedback-sound" type="checkbox" style="width:22px;height:22px">Scoring sounds</label><label style="display:flex;align-items:center;gap:10px;min-height:44px;color:#fff"><input id="feedback-haptics" type="checkbox" style="width:22px;height:22px">Haptic feedback</label><button id="feedback-test" type="button" style="margin-top:8px;min-height:44px;background:#f2bd45;color:#173044;border:0;border-radius:10px;font-weight:900">TEST SOUND</button><div id="feedback-test-status" role="status" style="color:#fff;margin-top:8px;font-size:13px"></div></div>'
index.write_text(text.replace(anchor,controls+anchor,1))
