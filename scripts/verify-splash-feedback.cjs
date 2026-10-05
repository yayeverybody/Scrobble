const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[2], 'utf8');
const css = fs.readFileSync(process.argv[3], 'utf8');
assert(css.includes('scrobbleSplashWave'));
assert(css.includes('scrobbleStudioPop'));
function setup({ reduced = false, muted = false, initial = 0, gated = false, prepare } = {}) {
  let time = initial, frame, hidden = false;
  const calls = [];
  const animations = Array.from({ length: 8 }, (_, i) => ({
    animationName: 'scrobbleSplashWave', currentTime: time, playState: 'running',
    effect: { getComputedTiming: () => ({ delay: 420 + i * 60, duration: 615 }) }
  }));
  animations.push({ animationName: 'scrobbleStudioPop', currentTime: time, playState: 'running', effect: { getComputedTiming: () => ({ delay: 1470, duration: 500 }) } });
  const splash = { getAnimations: () => animations, classList: { contains: () => hidden } };
  const gate = { pending: gated, contains() { return this.pending; }, remove() { this.pending = false; } };
  const rich = { prepare: prepare || (() => Promise.resolve()), play: options => { calls.push({ ...options, time }); return Promise.resolve(); }, cancel: () => Promise.resolve() };
  const ctx = {
    console, setTimeout, clearTimeout, performance: { now: () => time }, requestAnimationFrame(fn) { frame = fn; },
    localStorage: { getItem: key => muted && key === 'scrobble-feedback-haptics' ? 'off' : null },
    document: { documentElement: { classList: gate }, hidden: false, getElementById: id => id === 'scrobbleSplash' ? splash : null, addEventListener() {} },
    window: { matchMedia: () => ({ matches: reduced }), addEventListener() {}, Capacitor: { isNativePlatform: () => true, isPluginAvailable: () => true, Plugins: { Haptics: {}, ScrobbleFeedback: rich } } }
  };
  vm.createContext(ctx); vm.runInContext(source, ctx);
  return { calls, ctx, animations, gate, hide: () => { hidden = true; }, step(t) { time = t; animations.forEach(a => { a.currentTime = t; }); const fn = frame; frame = null; fn?.(); } };
}
(async () => {
const normal = setup();
for (let t = 0; t < 2200; t += 16) normal.step(t);
assert.equal(normal.calls.filter(c => c.kind === 'splashTile').length, 8);
assert.equal(normal.calls.filter(c => c.kind === 'splashStudio').length, 1);
assert(normal.calls.every(c => !c.sound && c.haptics));
normal.calls.slice(0, 8).forEach((call, i) => { const beat = 420 + i * 60; assert(call.time >= beat && call.time < beat + 16); });
assert(normal.calls.at(-1).time >= 1470);
normal.step(3000); assert.equal(normal.calls.length, 9, 'Animations must not replay feedback');
const late = setup({ initial: 2100 }); late.step(2100); assert.equal(late.calls.length, 0);
const reduced = setup({ reduced: true }); reduced.step(1000); assert.equal(reduced.calls.length, 0);
const hidden = setup(); hidden.hide(); hidden.step(1000); assert.equal(hidden.calls.length, 0);
const background = setup(); background.ctx.document.hidden = true; background.step(1000); assert.equal(background.calls.length, 0);
const muted = setup({ muted: true }); muted.step(432); assert(muted.calls.every(c => !c.haptics && !c.sound));
const paused = setup(); paused.animations.forEach(a => { a.playState = 'paused'; }); paused.step(432); assert.equal(paused.calls.length, 0);
let prepared;
const gated = setup({ gated: true, prepare: () => new Promise(resolve => { prepared = resolve; }) });
gated.step(432); assert.equal(gated.calls.length, 0); assert(gated.gate.pending);
prepared(); await new Promise(resolve => setImmediate(resolve));
assert.equal(gated.gate.pending, false);
gated.step(432); assert.equal(gated.calls.at(-1).kind, 'splashTile');
const failed = setup({ gated: true, prepare: () => Promise.reject(Error('no engine')) });
await new Promise(resolve => setImmediate(resolve)); assert.equal(failed.gate.pending, false);
console.log('PASS: all splash beats follow animation clocks once, silent splash, muted/reduced-motion/background/hidden suppression, no late-launch burst, and native preparation gates visual onset safely.');
})().catch(error => { console.error(error); process.exitCode = 1; });
