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


# Temporary Yay Everybody Popper Lab.
# Kept separate from Scrobble gameplay so this can become its own game module later.
index = Path('www/index.html')
text = index.read_text()
if 'id="ye-popper-lab"' not in text:
    popper_lab = r'''
<style id="ye-popper-lab-style">
#ye-popper-lab-launch{position:fixed;right:14px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:2147483000;border:0;border-radius:999px;background:#263b73;color:white;padding:12px 16px;font:800 13px Arial,sans-serif;box-shadow:0 4px 16px #0003}
#ye-popper-lab{display:none;position:fixed;inset:0;z-index:2147483001;background:#fff;color:#171717;font-family:Arial,sans-serif;overflow:auto;padding:calc(18px + env(safe-area-inset-top)) 18px calc(24px + env(safe-area-inset-bottom))}
#ye-popper-lab.open{display:block}
#ye-popper-lab .labbar{display:flex;align-items:center;justify-content:space-between;gap:12px;max-width:560px;margin:0 auto 20px}
#ye-popper-lab h2{margin:0;font-size:22px}
#ye-popper-lab .close{border:1px solid #bbb;background:#fff;border-radius:10px;padding:10px 14px;font-weight:800}
#ye-popper-lab .stage{max-width:560px;margin:auto;text-align:center}
#ye-popper-lab .base{width:min(82vw,390px);aspect-ratio:1/.55;margin:42px auto 20px;background:#d85b61;border-radius:50%;position:relative;box-shadow:0 18px 24px #0002}
#ye-popper-lab .field{position:absolute;left:8%;right:8%;top:8%;bottom:15%;border-radius:50%;background:#c8d82e;border:9px solid #27a8c6}
#ye-popper-lab .dome{position:absolute;left:14%;right:14%;top:-28%;height:92%;border-radius:50% 50% 46% 46%/70% 70% 30% 30%;background:linear-gradient(145deg,#ffffffb8,#d9f5ff38);border:2px solid #bfe9f3aa;box-shadow:inset -10px -10px 20px #9bd6e830;transform-origin:50% 100%;transition:transform 150ms ease-in}
#ye-popper-lab .dome.pop{transform:scaleX(.92) scaleY(.76)}
#ye-popper-lab .push{min-width:190px;min-height:54px;border:0;border-radius:16px;background:#263b73;color:#fff;font-weight:900;font-size:17px}
#ye-popper-lab .tests{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:18px}
#ye-popper-lab .tests button{min-height:44px;border:1px solid #bbb;border-radius:12px;background:#fff;padding:10px 14px;font-weight:800}
#ye-popper-lab .status{margin-top:14px;color:#666;font-size:13px}
</style>
<button id="ye-popper-lab-launch" type="button">POPPER LAB</button>
<section id="ye-popper-lab" aria-label="Popper haptic test">
  <div class="labbar"><h2>Popper Haptic Lab</h2><button class="close" type="button">CLOSE</button></div>
  <div class="stage">
    <div class="base"><div class="field"></div><div class="dome"></div></div>
    <button class="push" type="button">PUSH TO POP</button>
    <div class="tests">
      <button type="button" data-impact="LIGHT">Light</button>
      <button type="button" data-impact="MEDIUM">Medium</button>
      <button type="button" data-impact="HEAVY">Heavy</button>
    </div>
    <div class="status" aria-live="polite">Native haptics are checked when you tap.</div>
  </div>
</section>
<script id="ye-popper-lab-script">
(()=>{
 const launch=document.getElementById('ye-popper-lab-launch'),lab=document.getElementById('ye-popper-lab');
 const close=lab.querySelector('.close'),push=lab.querySelector('.push'),dome=lab.querySelector('.dome'),status=lab.querySelector('.status');
 const H=()=>window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.Haptics;
 async function impact(style){
   const h=H();
   if(!h){status.textContent='Native Haptics plugin is not available in this build.';return false}
   try{await h.impact({style});status.textContent='Native '+style.toLowerCase()+' impact fired.';return true}
   catch(e){status.textContent='Haptic error: '+(e&&e.message?e.message:String(e));return false}
 }
 launch.addEventListener('click',()=>lab.classList.add('open'));
 close.addEventListener('click',()=>lab.classList.remove('open'));
 lab.querySelectorAll('[data-impact]').forEach(b=>b.addEventListener('click',()=>impact(b.dataset.impact)));
 push.addEventListener('click',()=>{
   if(push.disabled)return; push.disabled=true; dome.classList.add('pop');
   impact('LIGHT');
   setTimeout(()=>{dome.classList.remove('pop');impact('HEAVY')},170);
   setTimeout(()=>{push.disabled=false;status.textContent='Pop complete: light compression + heavy snap at 170 ms.'},430);
 });
})();
</script>
'''
    text = text.replace('</body>', popper_lab + '\n</body>')
    index.write_text(text)
