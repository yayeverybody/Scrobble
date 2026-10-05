const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[2], 'utf8');
const css = fs.readFileSync(process.argv[3], 'utf8');
assert(css.includes('68%{transform:translateY(3px) scale(1.07)}'));
assert(css.includes('45%,55%'));
function setup({ reduced = false, muted = false, initial = 0 } = {}) {
  let time = initial, frame, hidden = false;
  const calls = [];
  const animations = Array.from({ length: 8 }, (_, i) => ({
    animationName: 'scrobbleSplashWave', currentTime: time, playState: 'running',
    effect: { getComputedTiming: () => ({ delay: 420 + i * 60, duration: 615 }) }
  }));
  animations.push({ animationName: 'scrobbleStudioPop', currentTime: time, playState: 'running', effect: { getComputedTiming: () => ({ delay: 1470, duration: 500 }) } });
  const splash = { getAnimations: () => animations, classList: { contains: () => hidden } };
  const rich = { play: options => { calls.push({ ...options, time }); return Promise.resolve(); }, cancel: () => Promise.resolve() };
  const ctx = {
    console, performance: { now: () => time }, requestAnimationFrame(fn) { frame = fn; },
    localStorage: { getItem: key => muted && key === 'scrobble-feedback-haptics' ? 'off' : null },
    document: { hidden: false, getElementById: id => id === 'scrobbleSplash' ? splash : null, addEventListener() {} },
    window: { matchMedia: () => ({ matches: reduced }), addEventListener() {}, Capacitor: { isNativePlatform: () => true, isPluginAvailable: () => true, Plugins: { Haptics: {}, ScrobbleFeedback: rich } } }
  };
  vm.createContext(ctx); vm.runInContext(source, ctx);
  return { calls, ctx, animations, hide: () => { hidden = true; }, step(t) { time = t; animations.forEach(a => { a.currentTime = t; }); const fn = frame; frame = null; fn?.(); } };
}
const normal = setup();
for (let t = 0; t < 2200; t += 16) normal.step(t);
assert.equal(normal.calls.filter(c => c.kind === 'splashTile').length, 8);
assert.equal(normal.calls.filter(c => c.kind === 'splashStudio').length, 1);
assert(normal.calls.every(c => !c.sound && c.haptics));
normal.calls.slice(0, 8).forEach((call, i) => { const beat = 420 + i * 60 + 615 * .68; assert(call.time >= beat && call.time < beat + 16); });
assert(normal.calls.at(-1).time >= 1470 + 500 * .45);
normal.step(3000); assert.equal(normal.calls.length, 9, 'Animations must not replay feedback');
const late = setup({ initial: 2100 }); late.step(2100); assert.equal(late.calls.length, 0);
const reduced = setup({ reduced: true }); reduced.step(1000); assert.equal(reduced.calls.length, 0);
const hidden = setup(); hidden.hide(); hidden.step(1000); assert.equal(hidden.calls.length, 0);
const background = setup(); background.ctx.document.hidden = true; background.step(1000); assert.equal(background.calls.length, 0);
const muted = setup({ muted: true }); muted.step(848); assert(muted.calls.every(c => !c.haptics && !c.sound));
const paused = setup(); paused.animations.forEach(a => { a.playState = 'paused'; }); paused.step(848); assert.equal(paused.calls.length, 0);
console.log('PASS: all splash beats follow animation clocks once, silent splash, muted/reduced-motion/background/hidden suppression, and no late-launch burst.');
