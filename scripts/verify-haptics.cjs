const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[2] || 'scripts/scrobble-haptics.js', 'utf8');
function setup({ native = true, fail = false, register = false } = {}) {
  const calls = [], listeners = {};
  const plugin = {
    impact(options) { calls.push({ method: 'impact', ...options }); return fail ? Promise.reject(Error('unavailable')) : Promise.resolve(); },
    notification(options) { calls.push({ method: 'notification', ...options }); return Promise.resolve(); }
  };
  const cap = { isNativePlatform: () => native, Plugins: register ? {} : { Haptics: plugin }, registerPlugin(name) { assert.equal(name, 'Haptics'); return plugin; } };
  const ctx = { window: { Capacitor: cap, addEventListener: (type, fn) => { listeners[type] = fn; } }, document: { addEventListener: (type, fn) => { listeners[type] = fn; } } };
  vm.createContext(ctx); vm.runInContext(source, ctx);
  const button = (id, disabled = false, cpu = false) => ({ id, disabled, getAttribute: () => null, hasAttribute: () => cpu });
  const click = (id, { trusted = true, disabled = false, cpu = false } = {}) => listeners.click({ isTrusted: trusted, target: { closest: () => button(id, disabled, cpu) } });
  return { ctx, calls, listeners, click };
}
(async () => {
  const s = setup();
  s.click('copyInvite'); s.click('shareInvite'); s.click('closeInvite');
  assert(s.calls.every(x => x.style === 'LIGHT'));
  s.click('startFriendGame'); s.click('cpu', { cpu: true });
  assert(s.calls.slice(-2).every(x => x.style === 'MEDIUM'));
  const count = s.calls.length;
  s.click('copyInvite', { disabled: true }); s.click('copyInvite', { trusted: false });
  assert.equal(s.calls.length, count);
  s.listeners.change({ isTrusted: true, target: { matches: () => true } });
  assert.equal(s.calls.at(-1).style, 'LIGHT');
  s.listeners['scrobble:turn-ended']({ detail: { move_type: 'play' } });
  assert.equal(s.calls.at(-1).type, 'SUCCESS');
  s.listeners['scrobble:turn-ended']({ detail: { move_type: 'swap' } });
  assert.equal(s.calls.at(-1).style, 'MEDIUM');
  const web = setup({ native: false }); web.click('shareInvite'); assert.equal(web.calls.length, 0);
  const fallback = setup({ register: true }); fallback.click('shareInvite'); assert.equal(fallback.calls.length, 1);
  const rejected = setup({ fail: true }); assert.doesNotThrow(() => rejected.click('copyInvite'));
  await new Promise(resolve => setImmediate(resolve));
  vm.runInContext(source, s.ctx);
  const before = s.calls.length; s.click('copyInvite'); assert.equal(s.calls.length, before + 1);
  console.log('PASS: native light/medium/success feedback; disabled and synthetic clicks ignored; web fallback, rejected plugin calls, and duplicate initialization remain safe.');
})().catch(error => { console.error(error); process.exitCode = 1; });
