const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const game = fs.readFileSync(process.argv[2], 'utf8');
const start = game.indexOf('function animateScoreValue('), end = game.indexOf('\nfunction render()', start);
assert(start >= 0 && end > start);
const source = game.slice(start, end);
for (const gain of [1, 5, 20, 100]) {
  let callback, time = 0, finished = false, lastReported = 10;
  const events = [];
  const el = { textContent: '10', classList: { remove() {}, add() {} }, offsetWidth: 1 };
  const feedback = {
    scoreCancel() {}, scoreStart() {},
    scoreProgress(slot, progress, now) {
      const visible = Number(el.textContent);
      assert.notEqual(visible, lastReported, 'Unchanged display frames must never trigger feedback');
      assert.equal(progress, (visible - 10) / gain, 'Feedback pitch/intensity must follow visible score progress');
      assert.equal(now, time);
      lastReported = visible;
      events.push({ visible, time });
    },
    scoreEnd() {
      assert.equal(Number(el.textContent), 10 + gain);
      assert.equal(events.at(-1).time, time, 'Payoff must fire on the final visible score change');
      finished = true;
    }
  };
  const ctx = {
    displayedScores: [10], scoreAnimations: [null], performance: { now: () => 0 },
    requestAnimationFrame(fn) { callback = fn; return 1; }, cancelAnimationFrame() {},
    window: { ScrobbleHaptics: feedback }
  };
  vm.createContext(ctx); vm.runInContext(source, ctx);
  ctx.animateScoreValue(el, 0, 10 + gain);
  for (time = 0; time <= 2016 && !finished; time += 16) callback(time);
  assert(finished); assert.equal(ctx.scoreAnimations[0], null);
  assert(events.at(-1).time <= 2000);
  assert(events.length <= gain);
}
console.log('PASS: score feedback follows visible increments for tiny/large gains; unchanged frames stay silent; payoff coincides with final displayed total.');
