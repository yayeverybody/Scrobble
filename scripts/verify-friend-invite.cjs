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
  const classes = new Set(hidden ? ['hidden'] : []), listeners = {};
  return {
    children: [], dataset: {}, style: {}, textContent: '',
    classList: {
      add: x => classes.add(x), remove: x => classes.delete(x),
      contains: x => classes.has(x),
      toggle(x, on) { if (on) classes.add(x); else classes.delete(x); }
    },
    appendChild(child) {
      if (child.parentNode) child.parentNode.children = child.parentNode.children.filter(x => x !== child);
      child.parentNode = this; this.children.push(child);
    },
    append(...children) { for(const child of children)this.appendChild(child); },
    insertBefore(child, before) { this.appendChild(child);this.children=this.children.filter(x=>x!==child);const i=this.children.indexOf(before);this.children.splice(i<0?this.children.length:i,0,child); },
    replaceChildren(...children) { this.children=[];this.append(...children); },
    contains(child) { return this.children.includes(child); },
    addEventListener(type, handler) { (listeners[type]||=[]).push(handler); },
    querySelectorAll() { return []; },
    click() { const result=this.onclick?.();for(const handler of listeners.click||[])handler();return result; }
  };
}
function setup(fail = false, direct = false, confirm = true, loseRules = false) {
  const ids = Object.fromEntries(['inviteBox', 'inviteLink', 'gameModeBox', 'closeGameMode', 'playFriendMode', 'playComputerMode', 'friendModePanel', 'computerModePanel', 'startFriendGame', 'sharedWeirdBox', 'gameModeTitle', 'newGameDash', 'closeInvite', 'copyInvite', 'shareInvite'].map(id => [id, element(true)]));
  const home = element(); home.appendChild(ids.inviteBox);home.appendChild(ids.newGameDash);
  const input = { value: 'high_roller', checked: false };
  ids.sharedWeirdBox.querySelectorAll = () => [input];
  const calls = { copy: [], share: [], rpc: [], alerts: [], confirmations: [] };
  const ctx = {
    document: { getElementById: id => ids[id], createElement: () => element() },
    inviteBox: ids.inviteBox, inviteLinkEl: ids.inviteLink,
    gameModeBox: ids.gameModeBox, closeGameMode: ids.closeGameMode, playFriendMode: ids.playFriendMode,
    user: { id: 'test' }, pendingNewGame: null,
    selectedWeirdRules: () => input.checked ? [input.value] : [],
    weirdRuleList: rules => rules.map(() => 'High Roller'),
    clearWeirdRules: () => { input.checked = false; }, code: () => 'TESTINVITE',
    client: { from: () => ({ select: () => ({ eq: () => ({ maybeSingle: async () => ({ data: null }) }) }) }) },
    window: { confirm(message) { calls.confirmations.push(message); return confirm; }, ScrobbleGame: {
      newGame(rules) { if (fail) throw Error('test preparation failure'); this.rules = rules; },
      exportState() { return { board: [], bag: [], racks: [[], []] }; }
    } },
    navigator: {
      clipboard: { async writeText(url) { calls.copy.push(url); } },
      async share(data) { calls.share.push(data); }
    },
    async rpc(name, args) { if(name==='scrobble_recent_opponents')return direct ? [{id:'friend',display_name:'Friend'}] : [];calls.rpc.push({ name, args }); return name === 'list_scrobble_games' ? [] : name === 'get_scrobble_game' ? {weird_rules: loseRules ? [] : ['high_roller']} : { id: 'created' }; },
    refreshGames: async () => {}, createComputerGame: () => {},
    alert: message => calls.alerts.push(message), setTimeout: () => {}
  };
  vm.createContext(ctx);
  vm.runInContext(between('  function inviteURL(', '  function code()') + '\n' + between('  function prepareFriendGame(', '  function askEndGame('), ctx);
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
  assert.deepEqual(Array.from(s.ctx.pendingNewGame.weirdRules), ['high_roller']);
  assert.equal(s.calls.rpc.length, 0, 'Preparation must not persist before copy/share');
  await s.ids.copyInvite.click();
  assert.equal(s.calls.copy[0], 'https://yayeverybody.com/?join=TESTINVITE');
  assert.equal(s.calls.rpc.filter(x => x.name === 'create_scrobble_game').length, 1);
  assert.deepEqual(Array.from(s.calls.rpc.find(x => x.name === 'set_scrobble_weird_rules').args.p_rules), ['high_roller']);
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
  const direct = setup(false, true);
  await direct.run('refreshRecentOpponents()');
  const sending = direct.run('recentItems.children[0].click()');
  assert(direct.ids.inviteBox.classList.contains('hidden'), 'Direct invites must never open the link share screen');
  assert(direct.home.contains(direct.ids.inviteBox), 'Direct invites must leave the share screen out of the setup panel');
  assert.equal(direct.ids.inviteBox.dataset.url, undefined);
  await sending;
  assert.match(direct.calls.confirmations[0], /Friend\?\s+High Roller/);
  assert.deepEqual(direct.calls.rpc.map(x => x.name), [
    'list_scrobble_games', 'create_scrobble_game', 'set_scrobble_weird_rules', 'set_scrobble_weird_rules', 'get_scrobble_game', 'send_scrobble_direct_invite'
  ]);
  assert.deepEqual(Array.from(direct.calls.rpc[2].args.p_rules), ['high_roller']);
  assert.equal(direct.calls.rpc[5].args.p_recipient_id, 'friend');
  const lost = setup(false, true, true, true);
  await lost.run('refreshRecentOpponents()');
  await lost.run('recentItems.children[0].click()');
  assert(!lost.calls.rpc.some(call=>call.name==='send_scrobble_direct_invite'), 'Never send an invitation when saved rules differ from confirmed rules');
  assert(lost.calls.alerts.some(message=>message.includes('not saved')));
  assert(lost.input.checked, 'Retain selections after a failed rule save');
  const skipped = setup(false, true, false);
  skipped.input.checked = false;
  await skipped.run('refreshRecentOpponents()');
  await skipped.run('recentItems.children[0].click()');
  assert.match(skipped.calls.confirmations[0], /Regular game/);
  assert.equal(skipped.calls.rpc.length, 0);
  console.log('PASS: inline invite, rule preservation, copy/share persistence, Done, reopen, computer switch, close, existing invites, and preparation failure.');
})().catch(error => { console.error(error); process.exitCode = 1; });
