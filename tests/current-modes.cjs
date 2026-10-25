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
  w.eval(read('game-engine-v3140.js').replace('if(!loadLocalState())freshLocalGame();','window.__modeTest={makeBag,realDictionaryLookup,tileValue,rackValue,scoreMove,cpuCrossInfo,setCell:(r,c,t)=>{board[r][c]=t}};if(!loadLocalState())freshLocalGame();'));
  await new Promise(r=>setTimeout(r,0));
  const normalValue=l=>l==='U'?2:1;
  const modes=['quad_chaos','name_dropper','vowels_are_worth_too_much'],names=['Crazy Random Bonus Spots','Name Dropper','Vowels Are Worth Too Much'];
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
    const bag=counts(w.__modeTest.makeBag());assert.deepEqual(bag,normal);
    for(const l of 'AEIOU')assert.equal(w.__modeTest.tileValue(l),mask&4?20:normalValue(l));
    assert.equal(w.__modeTest.tileValue('Y'),3);assert.equal(w.__modeTest.tileValue('Z'),10);
    assert.equal(w.__modeTest.rackValue(['A','E','I','O','U','Y']),mask&4?103:9);
    for(const rack of g.exportState().racks)assert(Array.from(rack).filter(l=>'AEIOU'.includes(l)).length>=2,'Opening vowel guarantee');
    const points=mask&4?20:1;
    const [r,c]=mask&1?[...w.document.querySelectorAll('#board .qw')].map(el=>[Number(el.dataset.r),Number(el.dataset.c)]).find(([r])=>r>0&&r<14):[7,7];
    w.__modeTest.setCell(r-1,c,{letter:'C',owner:0});w.__modeTest.setCell(r+1,c,{letter:'T',owner:0});
    assert.equal(w.__modeTest.cpuCrossInfo(r,c,'A',0,1).score,(points+5)*(mask&1?4:1));
    w.__modeTest.setCell(r,c,{letter:'A',pending:true,owner:0});
    assert.equal(w.__modeTest.scoreMove([{word:'CAT',cells:[[r-1,c],[r,c],[r+1,c]]}]),(points+5)*(mask&1?4:1));
    const rack=g.exportState().racks[0];
    for(let i=0;i<rack.length;i++)if('AEIOU'.includes(rack[i]))assert.equal(Number(w.document.querySelectorAll('#rack .rackbtn')[i].querySelector('.tilePointValue').textContent),mask&4?20:normalValue(rack[i]));
    const state=g.exportState();g.loadComputerState(state);assert.equal(w.document.getElementById('activeWeirdRules').textContent,label.textContent);
  }
  console.log('PASS: current options and labels, all 8 mode combinations, names gated from Classic, 20-point tile faces, human/CPU scores, 4x combinations and rack deductions, opening vowels, modern setup and Nudge retained');
}finally{dom?.window.close();fs.rmSync(dir,{recursive:true,force:true})}})().catch(e=>{console.error(e);process.exitCode=1});
