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

# Keep board presentation and delayed UI work scoped to the loaded game.
# Applied after extracting the archived mobile source, as with the other iOS fixes.
def replace_required(source, old, new):
    if old not in source:
        raise SystemExit('Game UI patch target missing: ' + old[:90])
    return source.replace(old, new, 1)

engine = Path('www/game-engine-v3140.js')
game = engine.read_text()
if 'function resetGamePresentation()' not in game:
    helpers = '''let gameGeneration=0;
function scheduleGameTask(callback,delay){
  const generation=gameGeneration;
  return setTimeout(()=>{if(generation===gameGeneration)callback()},delay)
}
function resetGamePresentation(){
  gameGeneration++;
  turnNoticeSummary=null;
  turnNoticeOverlay.classList.add('hidden');
  wordOverlay.classList.add('hidden');
  hideGameOver();noticeMode=false;
  clearTimeout(movePreviewTimer);movePreviewToken++;
  moveText.textContent='';status.textContent='';
  const bar=$('#lastPlayBar');if(bar)bar.textContent='';
  boardTransform.classList.remove('slowZoomOut');
  scoreAnimations.forEach(id=>{if(id)cancelAnimationFrame(id)});
  scoreAnimations=[null,null];displayedScores=[null,null];
}
function renderGameDetails(){
  const bar=$('#lastPlayBar');
  if(bar)bar.textContent=lastMoveSummary?.move_type==='play'?(lastMoveSummary.text||`${lastMoveSummary.playerName||'Player'} played ${(lastMoveSummary.words||[]).join(' / ')} for ${Number(lastMoveSummary.points)||0}`):'';
  const indicator=$('#activeWeirdRules');
  if(indicator){
    const names={all_or_none:'All or None',too_many_ts:'All or None',vowel_movement:'Vowel Movement',high_roller:'High Roller',too_many_tiles:'Too Many Tiles',seven_heaven:'Too Many Tiles',oops_all_ys:'Oops! All Y’s'};
    const active=[...new Set(weirdRules.map(id=>names[id]||id.replace(/_/g,' ')))];
    indicator.textContent=active.length?'Make it weird: '+active.join(' • '):'';
    indicator.hidden=!active.length;
  }
}
'''
    # Scope all existing delayed board UI operations; leave Promise timers intact
    # so in-flight operations can settle and check their generation afterward.
    game = game.replace('setTimeout(()=>', 'scheduleGameTask(()=>')
    game = replace_required(game, 'function hasWeirdRule(id)', helpers + 'function hasWeirdRule(id)')
    for old, new in [
        ('function freshLocalGame(){hideTurnNotice();hideGameOver();', 'function freshLocalGame(){resetGamePresentation();'),
        ("loadComputerState(s,difficulty='medium'){", "loadComputerState(s,difficulty='medium'){resetGamePresentation();"),
        ('loadCloudState(s,slot){', 'loadCloudState(s,slot){resetGamePresentation();'),
        ('render=function(){originalRender();', 'render=function(){originalRender();renderGameDetails();'),
        ('board,racks,scores,bag,current,committed,startingPlayer,\n      updatedAt', 'board,racks,scores,bag,current,committed,startingPlayer,weirdRules,\n      updatedAt'),
        ('  showTurnNotice(summary){showTurnNotice(summary)},', '  showTurnNotice(summary){showTurnNotice(summary)},\n  scheduleTask(callback,delay){return scheduleGameTask(callback,delay)},\n  leaveGame(){resetGamePresentation()},'),
        ('  if(!cpuMode||current!==1||cpuThinking)return;', '  if(!cpuMode||current!==1||cpuThinking)return;\n  const generation=gameGeneration;'),
        ('await new Promise(r=>setTimeout(r,850));', 'await new Promise(r=>setTimeout(r,850));\n  if(generation!==gameGeneration)return;'),
        ('const result=await realDictionaryLookup(w.word);\n      if(result.valid', 'const result=await realDictionaryLookup(w.word);\n      if(generation!==gameGeneration)return;\n      if(result.valid'),
        ('async function playMove(){', 'async function playMove(){\n  const generation=gameGeneration;'),
        ('for(const w of words)results.push(await realDictionaryLookup(w.word));', 'for(const w of words){results.push(await realDictionaryLookup(w.word));if(generation!==gameGeneration)return;}')
    ]:
        game = replace_required(game, old, new)
    engine.write_text(game)

app = Path('www/app-v3140.js')
app_text = app.read_text()
if 'window.ScrobbleGame.leaveGame();' not in app_text:
    app_text = replace_required(app_text, '  function showDash(){', '  function showDash(){\n    window.ScrobbleGame.leaveGame();')
    for old in [
        'setTimeout(()=>window.ScrobbleGame.showTurnNotice(rec.state.lastMoveSummary),180)',
        'setTimeout(()=>window.ScrobbleGame.showTurnNotice(summary),180)',
        'setTimeout(()=>window.ScrobbleGame.runComputerTurn(rec.difficulty),350)',
        'setTimeout(()=>window.ScrobbleGame.runComputerTurn(rec.difficulty),6000)'
    ]:
        app_text = replace_required(app_text, old, old.replace('setTimeout(', 'window.ScrobbleGame.scheduleTask('))
    app.write_text(app_text)

index = Path('www/index.html')
text = index.read_text()
if 'id="activeWeirdRules"' not in text:
    # The bar now renders from the loaded state instead of a global turn listener.
    text = replace_required(text, '<script src="last-play-v3120.js?v=312"></script>', '')
    text = replace_required(text, '</span></button></div></section>\n</div>', '</span></button></div><div id="activeWeirdRules" class="activeWeirdRules" hidden></div></section>\n</div>')
    text = replace_required(text, '</head>', '''<style>
#scrobble-v4 .activeWeirdRules{padding:6px 8px 2px;text-align:center;color:#d9efff;font:600 16.5px/1.35 Arial,Helvetica,sans-serif;overflow-wrap:anywhere}
#scrobble-v4 .activeWeirdRules[hidden]{display:none}
</style>
</head>''')
    index.write_text(text)

# Multiplayer stores only the signed-in player's rack locally. Never render the
# other player's (intentionally empty) array when the turn advances.
engine = Path('www/game-engine-v3140.js')
game = engine.read_text()
if 'let cloudRackMode=false;' not in game:
    game = replace_required(game, 'let gameGeneration=0;', 'let gameGeneration=0;\nlet cloudRackMode=false;')
    game = replace_required(game, 'function freshLocalGame(){resetGamePresentation();', 'function freshLocalGame(){resetGamePresentation();cloudRackMode=false;spectatorMode=false;')
    game = replace_required(game, "loadComputerState(s,difficulty='medium'){resetGamePresentation();", "loadComputerState(s,difficulty='medium'){resetGamePresentation();cloudRackMode=false;")
    game = replace_required(game, 'loadCloudState(s,slot){resetGamePresentation();', 'loadCloudState(s,slot){resetGamePresentation();cloudRackMode=true;')
    game = replace_required(game, 'const rackOwner=cpuMode?0:(spectatorMode?viewRackIndex:current);', 'const rackOwner=cpuMode?0:((cloudRackMode||spectatorMode)?viewRackIndex:current);')
    game = replace_required(game, "function render(){boardEl.innerHTML='';", "function render(){if(cloudRackMode&&current!==viewRackIndex)spectatorMode=true;boardEl.innerHTML='';")
    engine.write_text(game)
