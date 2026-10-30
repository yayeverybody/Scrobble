const {JSDOM}=require('jsdom'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const repo=path.resolve(__dirname,'..'),dir=fs.mkdtempSync(path.join(os.tmpdir(),'scrobble-ad-'));
(async()=>{try{
 execFileSync('python3',[path.join(repo,'scripts/prepare-board-tests.py'),dir]);
 const root=path.join(dir,'scrobble-mobile/www'),html=fs.readFileSync(path.join(root,'index.html'),'utf8'),app=fs.readFileSync(path.join(root,'app-v3140.js'),'utf8');
 const dom=new JSDOM(html,{runScripts:'outside-only',url:'http://localhost'}),w=dom.window;
 w.Math.random=()=>0;
 w.eval(fs.readFileSync(path.join(root,'mirrors-ad.js'),'utf8'));
 const ad=w.document.getElementById('mirrorsAd'),close=w.document.getElementById('mirrorsAdClose');let home=0;
 w.addEventListener('scrobble:home',()=>home++);
 assert(ad.hidden);w.ScrobbleFakeAd.show();assert(ad.hidden,'Never show on Games');
 w.document.body.classList.add('scrobbleGameActive');w.ScrobbleFakeAd.show();assert(!ad.hidden);assert.equal(w.document.activeElement,close);
 assert.equal(w.document.getElementById('mirrorsAdTitle').textContent,'Mirrors.');
 assert.equal(w.document.getElementById('mirrorsAdTagline').textContent,'Reflect yourself back to yourself.');
 assert(fs.statSync(path.join(root,'fake-ads/mirrors.jpg')).size>10000);
 close.click();assert(ad.hidden);assert.equal(home,1);close.click();assert.equal(home,1,'Dismiss only once');
 w.ScrobbleFakeAd.show();const token=w.ScrobbleFakeAd.viewToken;w.ScrobbleFakeAd.reset();assert(ad.hidden);assert(w.ScrobbleFakeAd.viewToken>token);
 const seen=new Set([ad.dataset.sponsor]);let previous=ad.dataset.sponsor;
 for(let i=0;i<120;i++){
  w.Math.random=()=>(i%11)/11;w.ScrobbleFakeAd.show();
  const id=ad.dataset.sponsor;assert.notEqual(id,previous,'No consecutive sponsor repeats');seen.add(id);previous=id;
  assert.equal(w.localStorage.getItem('scrobble-last-fictional-sponsor'),id);
  assert(w.document.getElementById('fakeAdArtwork').src.endsWith('/fake-ads/'+id+'.jpg'));
  assert(fs.statSync(path.join(root,'fake-ads',id+'.jpg')).size>10000);
  if(id==='clear-spaghetti-sauce')assert.equal(w.document.getElementById('mirrorsAdTagline').textContent,'You can’t see it!');
  if(id==='neon-green'){assert.equal(w.document.getElementById('mirrorsAdTitle').textContent,'Neon Green');assert.equal(ad.querySelector('.mirrorFooter').textContent,'From the makers of Reflective Orange.');}
  if(id==='ceiling-carpet')assert.equal(w.document.getElementById('mirrorsAdTagline').textContent,'Shut up. You’re stupid.');
  if(id==='high-cut-jean-shorts')assert.equal(w.document.querySelector('.mirrorFooter').textContent,'Mobility Unmatched');
  if(id==='splashless-chili')assert.equal(w.document.querySelector('.mirrorFooter').textContent,'');
  if(id==='powdered-water')assert.equal(w.document.querySelector('.mirrorFooter').textContent,'ORIGINAL FLAVOR');
  if(id==='foil-ball')assert.equal(w.document.querySelector('.mirrorFooter').textContent,'ENDLESSLY ENTERTAINING');
  if(id==='invest-in-glass')assert.equal(w.document.querySelector('.mirrorFooter').textContent,'TURN GOLD INTO GLASS');
  w.ScrobbleFakeAd.reset();
 }
 assert.equal(seen.size,12,'All twelve sponsors are available');
 const reopened=new JSDOM(html,{runScripts:'outside-only',url:'http://localhost'});
 reopened.window.localStorage.setItem('scrobble-last-fictional-sponsor',previous);
 reopened.window.Math.random=()=>0;
 reopened.window.eval(fs.readFileSync(path.join(root,'mirrors-ad.js'),'utf8'));
 reopened.window.document.body.classList.add('scrobbleGameActive');reopened.window.ScrobbleFakeAd.show();
 assert.notEqual(reopened.window.document.getElementById('mirrorsAd').dataset.sponsor,previous,'No repeat across app launches');
 reopened.window.close();dom.window.close();
 const block=app.slice(app.indexOf("  window.addEventListener('scrobble:turn-ended',async e=>{"),app.indexOf("  window.addEventListener('scrobble:challenge-created'"));
 for(const scenario of ['human','cpu','pass','swap','cloud','failed','navigated']){
  const tasks=[],ads=[],ctx={currentComputer:['human','cpu'].includes(scenario),currentGame:'one',currentSlot:1,statusEl:{},user:{},myProfile:{},saveCurrentComputerGame(){},loadComputerRecord:()=>({id:'cpu'}),rpc:async()=>{if(scenario==='failed')throw Error('save failed');if(scenario==='navigated')ctx.window.ScrobbleFakeAd.viewToken++;return{}},sleep:async()=>{},refreshCurrentCloudGame:async()=>{},refreshGames:async()=>{},accountDisplayName:()=>'',profileLabel:()=>'',alert(){},document:{body:{classList:{contains:()=>false}}},window:{ScrobbleFakeAd:{viewToken:1,show:()=>ads.push('ad'),afterTurn:()=>tasks.push({fn:()=>ads.push('ad'),ms:1600})},ScrobbleGame:{scheduleTask:(fn,ms)=>tasks.push({fn,ms}),exportState:()=>({racks:[[],[]],board:[],bag:[],scores:[0,0]}),runComputerTurn(){}},addEventListener:(event,fn)=>ctx.handler=fn}};
  vm.createContext(ctx);vm.runInContext(block,ctx);
  await ctx.handler({detail:{move_type:['pass','swap'].includes(scenario)?scenario:'play',playedBy:scenario==='cpu'?1:0,words:['CAT'],points:3}});
  const sponsor=tasks.filter(t=>t.ms===1600);assert.equal(sponsor.length,['human','cloud'].includes(scenario)?1:0,scenario);
  for(const t of sponsor)t.fn();assert.equal(ads.length,sponsor.length);
 }
 assert(app.includes('window.ScrobbleFakeAd?.reset();'),'Navigation resets stale ad eligibility');
 console.log('PASS: all twelve sponsors, 120 nonrepeating rotations, persisted choice across launches, exact text, bundled art, close-to-games event, focus, no duplicate dismissal, saved human turns only, failed saves/pass/swap/CPU/navigation excluded');
}finally{fs.rmSync(dir,{recursive:true,force:true})}})().catch(e=>{console.error(e);process.exitCode=1});
