from pathlib import Path

index = Path('www/index.html')
s = index.read_text()
start = s.index('<script type="module" id="scrobble-ios-universal-links">')
end = s.index('</script>', start) + len('</script>')
s = s[:start] + '''<script type="module" id="scrobble-ios-universal-links">
(async()=>{
  if(!window.Capacitor?.isNativePlatform?.())return;
  const App=window.Capacitor?.Plugins?.App;if(!App)return;
  let lastDelivery='',lastTime=0;
  const routeInvite=incoming=>{
    try{
      const u=new URL(incoming);
      if(u.protocol!=='https:'||!['yayeverybody.com','www.yayeverybody.com'].includes(u.hostname.toLowerCase()))return;
      const join=u.searchParams.get('join');if(join===null)return;
      if(!/^[a-z0-9_-]{1,128}$/i.test(join)){window.dispatchEvent(new CustomEvent('scrobble:invite-error'));return}
      const now=Date.now();if(lastDelivery===join&&now-lastTime<1500)return;
      lastDelivery=join;lastTime=now;
      history.replaceState({},'','/?join='+encodeURIComponent(join));
      window.dispatchEvent(new CustomEvent('scrobble:native-invite'));
    }catch(e){console.warn('Could not read invitation',e);window.dispatchEvent(new CustomEvent('scrobble:invite-error'))}
  };
  // Register warm deliveries first. Never reload and reconsume getLaunchUrl.
  await App.addListener('appUrlOpen',({url})=>routeInvite(url));
  try{const launch=await App.getLaunchUrl();if(launch?.url)routeInvite(launch.url)}catch(e){console.warn('Could not read launch invitation',e)}
})();
</script>''' + s[end:]
index.write_text(s)

app=Path('www/app-v3140.js');s=app.read_text()
s=s.replace('  async function joinFromURL(){', '''  let inviteRequest=0;
  window.addEventListener('scrobble:native-invite',()=>{
    if(client&&user){
      window.ScrobbleGame.prepareForHome();
      if(currentComputer)saveCurrentComputerGame();
      showDash();
      joinFromURL().catch(()=>{statusEl.textContent='Invitation could not be loaded. Please try the link again.'});
    }
  });
  window.addEventListener('scrobble:invite-error',()=>{statusEl.textContent='Invitation could not be loaded. Please ask for a new link.'});
  async function joinFromURL(){
    const request=++inviteRequest;''',1)
s=s.replace('pendingJoinCode=join.toUpperCase();', 'pendingJoinCode=join.toUpperCase();\n    const requestedCode=pendingJoinCode;',1)
s=s.replace("const info=await rpc('get_scrobble_invite_weirdness',{p_invite_code:pendingJoinCode});", """const info=await Promise.race([
        rpc('get_scrobble_invite_weirdness',{p_invite_code:requestedCode}),
        new Promise((_,reject)=>setTimeout(()=>reject(new Error('Invitation lookup timed out')),5000))
      ]);
      if(request!==inviteRequest)return;""",1)
s=s.replace("    joinBox.classList.remove('hidden');\n  }\n  async function confirmJoinGame", "    if(request===inviteRequest)joinBox.classList.remove('hidden');\n  }\n  async function confirmJoinGame",1)
# Delayed CPU callbacks must belong to the game that scheduled them.
s=s.replace("if(rec&&e.detail?.playedBy===0)setTimeout(()=>window.ScrobbleGame.runComputerTurn(rec.difficulty),6000);", "if(rec&&e.detail?.playedBy===0)setTimeout(()=>{if(currentComputer&&loadComputerRecord()?.id===rec.id)window.ScrobbleGame.runComputerTurn(rec.difficulty)},6000);")
s=s.replace("if((rec.state?.current||0)===1)setTimeout(()=>window.ScrobbleGame.runComputerTurn(rec.difficulty),350)", "if((rec.state?.current||0)===1)setTimeout(()=>{if(currentComputer&&loadComputerRecord()?.id===rec.id)window.ScrobbleGame.runComputerTurn(rec.difficulty)},350)")
app.write_text(s)

engine=Path('www/game-engine-v3140.js');s=engine.read_text()
s=s.replace('async function runComputerTurn(difficulty=cpuDifficulty){','let cpuGeneration=0;\nasync function runComputerTurn(difficulty=cpuDifficulty){',1)
s=s.replace("  cpuThinking=true;cpuDifficulty=difficulty||'medium';", "  const generation=cpuGeneration;\n  const validTurn=()=>generation===cpuGeneration&&cpuMode&&current===1;\n  cpuThinking=true;cpuDifficulty=difficulty||'medium';",1)
s=s.replace('  const remaining=cpuFindMoves();','  if(!validTurn())return;\n  const remaining=cpuFindMoves();',1)
start=s.index('async function runComputerTurn(')
head,tail=s[:start],s[start:]
tail=tail.replace('      const result=await realDictionaryLookup(w.word);','      const result=await realDictionaryLookup(w.word);\n      if(!validTurn())return;',1)
s=head+tail
s=s.replace('function freshLocalGame(){','function freshLocalGame(){cpuGeneration++;',1)
s=s.replace("loadComputerState(s,difficulty='medium'){", "loadComputerState(s,difficulty='medium'){cpuGeneration++;",1)
s=s.replace('  loadCloudState(s,slot){','  loadCloudState(s,slot){cpuGeneration++;',1)
s=s.replace('prepareForHome(){if(pending.length)recall();', 'prepareForHome(){cpuGeneration++;cpuThinking=false;if(pending.length)recall();',1)
anchor='selected=null;pending=[];awaiting=null;cloudChallenge=null;pendingChallengeConfirm=null;swapMode=false;swapSelected.clear();spectatorMode=false;'
replacement="""for(let r=0;r<board.length;r++)for(let c=0;c<board[r].length;c++){
      const tile=board[r][c];if(tile?.pending){racks[tile.owner===1?1:0].push(tile.letter);board[r][c]=null}
    }
    """+anchor
assert s.count(anchor)==1
s=s.replace(anchor,replacement,1);engine.write_text(s)
