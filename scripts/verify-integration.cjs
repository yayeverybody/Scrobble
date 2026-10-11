const fs=require('node:fs'),assert=require('node:assert/strict');
const root=process.argv[2]||'www';
const engine=fs.readFileSync(root+'/game-engine-v3140.js','utf8');
const html=fs.readFileSync(root+'/index.html','utf8');
const app=fs.readFileSync(root+'/app-v3140.js','utf8');
for(const part of ['ensureOpeningVowels(0);ensureOpeningVowels(1)','function ensureOpeningVowels(player)']){
  assert(engine.includes(part),'Missing opening-rack/endgame code: '+part);
}
assert(html.includes('weirdChoice strong{font-size:21px'),'Make It Weird titles lost styling');
for(const id of ['playComputerMode','friendModePanel','sharedWeirdBox']){
  assert(html.includes('id="'+id+'"'),'Missing modern game setup: '+id);
}
assert(app.includes('nudgeGame'),'Missing nudge handler');
console.log('PASS: opening vowels, modern setup, Nudge and mode headings are packaged');
