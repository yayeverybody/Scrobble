const fs=require('node:fs'),assert=require('node:assert/strict');
const s=fs.readFileSync(process.argv[2]||'www/game-engine-v3140.js','utf8');
assert(s.includes('SSA national baby names, imported at build time'),'SSA list absent');
assert(s.includes("for(const n of '"),'SSA names not populated');
assert(s.includes("properNouns.add(n)"),'SSA names not inserted into allowlist');
assert(s.includes("hasWeirdRule('name_dropper')&&properNouns.has(word.toUpperCase())"),'Name Dropper rule gate missing');
assert(s.includes('SARA SARAH'),'Common name variants absent from curated list');
assert(s.includes('pendingChallengeConfirm'),'Opponent review missing');
console.log('PASS: SSA names loaded into Name Dropper, existing rule gate and review preserved');
