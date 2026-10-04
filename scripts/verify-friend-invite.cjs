const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const www = process.argv[2] || 'www';
const app = fs.readFileSync(path.join(www, 'app-v3140.js'), 'utf8');
const html = fs.readFileSync(path.join(www, 'index.html'), 'utf8');
function between(start, end) {
  const from = app.indexOf(start), to = app.indexOf(end, from);
  assert(from >= 0 && to > from, `Missing source block: ${start}`);
  return app.slice(from, to);
}
function element(hidden = false) {
  const classes = new Set(hidden ? ['hidden'] : []);
  return {
    children: [], dataset: {}, textContent: '',
    classList: {
      add: x => classes.add(x), remove: x => classes.delete(x),
      contains: x => classes.has(x),
      toggle(x, on) { if (on) classes.add(x); else classes.delete(x); }
    },
    appendChild(child) {
      if (child.parentNode) child.parentNode.children = child.parentNode.children.filter(x => x !== child);
      child.parentNode = this; this.children.push(child);
    },
    contains(child) { return this.children.includes(child); },
    addEventListener(type, handler) { this[type] = handler; },
    querySelectorAll() { return []; },
    click() { return this.onclick(); }
  };
}
function setup(fail = false) {
  const ids = Object.fromEntries(['inviteBox', 'inviteLink', 'gameModeBox', 'closeGameMode', 'playFriendMode', 'playComputerMode', 'friendModePanel', 'computerModePanel', 'startFriendGame', 'sharedWeirdBox', 'gameModeTitle', 'newGameDash', 'closeInvite', 'copyInvite', 'shareInvite'].map(id => [id, element(true)]));
  const home = element(); home.appendChild(ids.inviteBox);
  const input = { value: 'high_roller', checked: false };
  ids.sharedWeirdBox.querySelectorAll = () => [input];
  const calls = { copy: [], share: [], rpc: [], alerts: [] };
  const ctx = {
    document: { getElementById: id => ids[id] },
    inviteBox: ids.inviteBox, inviteLinkEl: ids.inviteLink,
    gameModeBox: ids.gameModeBox, closeGameMode: ids.closeGameMode, playFriendMode: ids.playFriendMode,
    user: { id: 'test' }, pendingNewGame: null,
    selectedWeirdRules: () => input.checked ? [input.value] : [],
    clearWeirdRules: () => { input.checked = false; }, code: () => 'TESTINVITE',
    window: { ScrobbleGame: {
      newGame(rules) { if (fail) throw Error('test preparation failure'); this.rules = rules; },
      exportState() { return { board: [], bag: [], racks: [[], []], weirdRules: this.rules }; }
    } },
    navigator: {
      clipboard: { async writeText(url) { calls.copy.push(url); } },
      async share(data) { calls.share.push(data); }
    },
    async rpc(name, args) { calls.rpc.push({ name, args }); return name === 'list_scrobble_games' ? [] : { id: 'created' }; },
    refreshGames: async () => {}, createComputerGame: () => {},
    alert: message => calls.alerts.push(message), setTimeout: () => {}
  };
  vm.createContext(ctx);
  vm.runInContext(between('  function inviteURL(', '  function code()') + '\n' + between('  async function createGame(){', '  function askEndGame('), ctx);
  const run = code => vm.runInContext(code, ctx);
  ids.newGameDash.click(); ids.playFriendMode.click(); input.checked = true;
  return { ids, input, calls, ctx, run, home };
}
(async () => {
  assert(html.includes('#friendModePanel #inviteBox{position:static'));
  assert(html.includes('<h2>Invite a friend</h2>'));
  assert.equal((html.match(/id="inviteBox"/g) || []).length, 1);
  const s = setup(); await s.ids.startFriendGame.click();
  assert(s.ids.friendModePanel.contains(s.ids.inviteBox));
  assert(!s.ids.gameModeBox.classList.contains('hidden'));
  assert(!s.ids.inviteBox.classList.contains('hidden'));
  assert(s.ids.sharedWeirdBox.classList.contains('hidden'));
  assert(s.ids.startFriendGame.classList.contains('hidden'));
  assert.deepEqual(s.ctx.pendingNewGame.weirdRules, ['high_roller']);
  assert.equal(s.calls.rpc.length, 0, 'Preparation must not persist before copy/share');
  await s.ids.copyInvite.click();
  assert.equal(s.calls.copy[0], 'https://yayeverybody.com/?join=TESTINVITE');
  assert.equal(s.calls.rpc.filter(x => x.name === 'create_scrobble_game').length, 1);
  assert.deepEqual(s.calls.rpc.find(x => x.name === 'set_scrobble_weird_rules').args.p_rules, ['high_roller']);
  s.ids.closeInvite.click();
  assert(s.ids.gameModeBox.classList.contains('hidden'));
  assert(s.home.contains(s.ids.inviteBox));
  s.ids.newGameDash.click(); s.ids.playFriendMode.click();
  assert(!s.ids.startFriendGame.classList.contains('hidden'));
  assert(s.ids.inviteBox.classList.contains('hidden'));
  const share = setup(); await share.ids.startFriendGame.click(); await share.ids.shareInvite.click();
  assert.equal(share.calls.share[0].url, 'https://yayeverybody.com/?join=TESTINVITE');
  assert.equal(share.calls.rpc.filter(x => x.name === 'create_scrobble_game').length, 1);
  const cancelled = setup(); await cancelled.ids.startFriendGame.click();
  cancelled.ids.playComputerMode.click();
  assert.equal(cancelled.ctx.pendingNewGame, null);
  assert(cancelled.home.contains(cancelled.ids.inviteBox));
  assert(!cancelled.ids.computerModePanel.classList.contains('hidden'));
  assert.equal(cancelled.calls.rpc.length, 0);
  const closed = setup(); await closed.ids.startFriendGame.click(); closed.ids.closeGameMode.click();
  assert.equal(closed.ctx.pendingNewGame, null);
  assert(closed.home.contains(closed.ids.inviteBox));
  const existing = setup(); existing.run("openInvite('EXISTING')");
  assert(existing.home.contains(existing.ids.inviteBox));
  assert(existing.ids.gameModeBox.classList.contains('hidden'));
  assert.equal(existing.ids.inviteBox.dataset.code, 'EXISTING');
  const failed = setup(true); await failed.ids.startFriendGame.click();
  assert(!failed.ids.gameModeBox.classList.contains('hidden'));
  assert(!failed.ids.startFriendGame.classList.contains('hidden'));
  assert(failed.input.checked);
  assert.equal(failed.calls.alerts.length, 1);
  console.log('PASS: inline invite, rule preservation, copy/share persistence, Done, reopen, computer switch, close, existing invites, and preparation failure.');
})().catch(error => { console.error(error); process.exitCode = 1; });
