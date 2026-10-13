const fs=require('node:fs'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2]||'www/game-engine-v3140.js','utf8');
assert(source.includes('const properNouns=new Set(('),'Curated Name Dropper list missing');
assert(source.includes('SARA SARAH'),'Common first names missing');
assert(source.includes("hasWeirdRule('name_dropper')&&properNouns.has(word.toUpperCase())"),'Name Dropper rule gate missing');
assert(source.includes('pendingChallengeConfirm'),'Opponent review path missing');
console.log('PASS: offline Name Dropper names, mode gating and opponent review');
