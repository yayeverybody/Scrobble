// Install jsdom, then run: node tests/current-modes.cjs
const {JSDOM}=require('jsdom');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const repo=path.resolve(__dirname,'..'),dir=fs.mkdtempSync(path.join(os.tmpdir(),'scrobble-modes-'));
(async()=>{let dom;try{
  execFileSync('python3',[path.join(repo,'scripts/prepare-board-tests.py'),dir]);
  const read=name=>fs.readFileSync(path.join(dir,'scrobble-mobile/www',name),'utf8');
  dom=new JSDOM(read('index.html'),{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
  const w=dom.window;w.fetch=async()=>({ok:true,text:async()=>read('scrobble-classic-lexicon.txt')});w.Element.prototype.scrollIntoView=function(){};
  w.eval(read('game-engine-v3140.js').replace('if(!loadLocalState())freshLocalGame();','window.__modeTest={makeBag,realDictionaryLookup};if(!loadLocalState())freshLocalGame();'));
  await new Promise(r=>setTimeout(r,0));
  const modes=['quad_chaos','name_dropper','suffix_suffocation'],names=['Crazy Random Bonus Spots','Name Dropper','Suffixly'];
  assert.deepEqual([...w.document.querySelectorAll('.weirdChoice input')].map(i=>i.value),modes);
  assert(w.document.getElementById('playComputerMode'));assert(w.document.getElementById('friendModePanel'));assert(read('app-v3140.js').includes('nudgeGame'));
  const g=w.ScrobbleGame,counts=bag=>Array.from(bag).reduce((o,l)=>(o[l]=(o[l]||0)+1,o),{});
  g.newComputerGame('easy',[]);const normal=counts(w.__modeTest.makeBag());
  const classicName=await w.__modeTest.realDictionaryLookup('SARAH');assert.equal(classicName.valid,false);
  for(let mask=0;mask<8;mask++){
    const rules=modes.filter((_,i)=>mask&(1<<i));g.newComputerGame('easy',rules);
    const label=w.document.getElementById('activeWeirdRules');for(let i=0;i<3;i++)assert.equal(label.textContent.includes(names[i]),!!(mask&(1<<i)));
    assert.equal(w.document.querySelectorAll('#board .qw').length,mask&1?5:0);
    const name=await w.__modeTest.realDictionaryLookup('SARAH');assert.equal(name.valid,!!(mask&2));
    const unknown=await w.__modeTest.realDictionaryLookup('ZZZQXJZZ');assert.equal(unknown.valid,false,'Unknown names remain subject to review');
    const bag=counts(w.__modeTest.makeBag());for(const [l,extra] of Object.entries({S:4,D:3,R:3,Y:2}))assert.equal(bag[l],normal[l]+(mask&4?extra:0));
    for(const rack of g.exportState().racks)assert(Array.from(rack).filter(l=>'AEIOU'.includes(l)).length>=2,'Opening vowel guarantee');
    const state=g.exportState();g.loadComputerState(state);assert.equal(w.document.getElementById('activeWeirdRules').textContent,label.textContent);
  }
  console.log('PASS: current options and labels, all 8 mode combinations, names gated from Classic, suffix distribution, opening vowels, modern setup and Nudge retained');
}finally{dom?.window.close();fs.rmSync(dir,{recursive:true,force:true})}})().catch(e=>{console.error(e);process.exitCode=1});
