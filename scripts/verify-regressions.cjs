const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const www=process.argv[2],html=fs.readFileSync(path.join(www,'index.html'),'utf8'),game=fs.readFileSync(path.join(www,'game-engine-v3140.js'),'utf8');
(async()=>{
  const source=html.match(/<script type="module" id="scrobble-ios-universal-links">([\s\S]*?)<\/script>/)[1];
  let listener;const events=[],urls=[];
  const ctx={URL,Date,console,history:{replaceState:(_,__,url)=>urls.push(url)},CustomEvent:class{constructor(type){this.type=type}},window:{dispatchEvent:e=>events.push(e.type),Capacitor:{isNativePlatform:()=>true,Plugins:{App:{addListener:async(_,fn)=>{listener=fn},getLaunchUrl:async()=>({url:'https://yayeverybody.com/?join=FIRST'})}}}},location:{replace(){throw Error('WebView reloaded')}}};
  vm.createContext(ctx);await vm.runInContext(source,ctx);
  assert.equal(urls.length,1);assert.equal(events[0],'scrobble:native-invite');
  listener({url:'https://yayeverybody.com/?join=FIRST'});assert.equal(urls.length,1);
  listener({url:'https://yayeverybody.com/?join=SECOND'});assert.equal(urls.length,2);
  listener({url:'https://evil.yayeverybody.com/?join=OTHER'});assert.equal(urls.length,2);
  listener({url:'https://yayeverybody.com/?join=%3Cbad%3E'});assert.equal(events.at(-1),'scrobble:invite-error');
  // New web document with the same cold-launch URL still must not reload.
  await vm.runInContext(source,ctx);assert.equal(urls.length,3);
  const cpu=game.slice(game.indexOf('let cpuGeneration=0;'),game.indexOf('\nfunction saveLocalState()'));
  const empty=()=>Array.from({length:15},()=>Array(15).fill(null));
  let resolveLookup,commits=0;
  const c={cpuMode:true,current:1,cpuThinking:false,cpuDifficulty:'medium',selected:null,swapMode:false,swapSelected:new Set(),render(){},offlineLexiconReadyPromise:Promise.resolve(),setTimeout:fn=>{fn()},board:empty(),racks:[[],['D','E']],pending:[],cpuFindMoves:()=>[{newTiles:[{r:7,c:7,letter:'D'},{r:7,c:8,letter:'E'}]}],cpuChooseMove:a=>a[0],validationError:()=>null,moveWords:()=>[{word:'DE',cells:[[7,7],[7,8]]}],realDictionaryLookup:()=>new Promise(r=>{resolveLookup=r}),recall(){throw Error('Stale recall')},scoreMove:()=>3,commit(){commits++;c.current=0},cpuSwapOrPass(){throw Error('Unexpected pass')}};
  vm.createContext(c);vm.runInContext(cpu,c);
  const old=vm.runInContext('runComputerTurn()',c);for(let i=0;i<5;i++)await Promise.resolve();assert(resolveLookup);
  // Loading another state while dictionary lookup is in flight cancels old work.
  vm.runInContext('cpuGeneration++;cpuThinking=false',c);c.board=empty();c.racks=[[],['D','E']];c.pending=[];
  resolveLookup({valid:true});await old;assert.equal(commits,0);assert(c.board.flat().every(x=>x===null));
  const fresh=vm.runInContext('runComputerTurn()',c);for(let i=0;i<5;i++)await Promise.resolve();
  resolveLookup({valid:true});await fresh;assert.equal(commits,1);assert.equal(c.board.flat().filter(Boolean).length,2);
  console.log('PASS: cold/warm invitations, duplicate delivery, malformed links, repeated launch URL, stale CPU lookup cancellation and one committed placement.');
})();
