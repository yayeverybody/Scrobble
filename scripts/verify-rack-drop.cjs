const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const app = fs.readFileSync(process.argv[2], 'utf8');
function extract(start, end) {
  const i = app.indexOf(start), j = app.indexOf(end, i);
  assert(i >= 0 && j > i);
  return app.slice(i, j);
}
const targetSource = extract('function targetAt(', 'function startDrag(');
const endSource = extract('function endDrag(', 'function wireDrag(');
const rect = (left, top, right, bottom) => ({ left, top, right, bottom, width: right-left, height: bottom-top });
const noop = () => {};
function setup(tileRect) {
  const classList = { add: noop, remove: noop };
  const area = { getBoundingClientRect: () => rect(0, 600, 400, 750), querySelector: () => ({ getBoundingClientRect: () => rect(0, 680, 400, 750) }) };
  const rack = { getBoundingClientRect: () => rect(12, 610, 388, 675), closest: () => area, classList };
  const board = Array.from({ length: 15 }, () => Array(15).fill(null));
  board[14][5] = { letter: 'A', pending: true, owner: 0 };
  let renders = 0, reordered = null;
  const feedback = [];
  const ctx = { window: { ScrobbleHaptics: { tile: () => feedback.push("tile"), tileReturn: () => feedback.push("return") } },
    root: { querySelectorAll: () => [] }, rackEl: rack, swapMode: false,
    swapTrayTiles: { getBoundingClientRect: () => rect(0, 500, 400, 560), classList },
    pointInRect: (x,y,r) => x>=r.left && x<=r.right && y>=r.top && y<=r.bottom,
    boardTargetAt: () => ({ type: 'board', r: 14, c: 6 }),
    boardEl: { querySelector: () => ({ classList }) },
    drag: { origin: { type: 'board', r: 14, c: 5 }, source: { classList }, ghost: { querySelector: () => ({ getBoundingClientRect: () => tileRect }), remove: noop } },
    board, racks: [[], []], current: 0, pending: [{ r:14, c:5, letter:'A' }],
    removePending(r,c) { ctx.pending = ctx.pending.filter(p => p.r!==r || p.c!==c); },
    moveGhost: noop, render: () => { renders++; }, selected: 1,
    reorderRack: (a,b) => { reordered = [a,b]; }, rackDropIndex: () => 2,
    setTimeout: noop, focusCell: noop, pinch: null, panGesture: null
  };
  vm.createContext(ctx); vm.runInContext(targetSource + '\n' + endSource, ctx);
  return { ctx, feedback, renders: () => renders, reordered: () => reordered };
}
// Subpixel overlaps on every edge beat the board's forgiving snap zone.
for (const r of [rect(100, 560, 140, 600.1), rect(-39.9, 620, 0.1, 660), rect(399.9, 620, 439.9, 660), rect(100, 679.9, 140, 719.9)]) {
  const s = setup(r); assert.equal(s.ctx.targetAt(200, 580).type, 'rack');
}
const bottomBoard = setup(rect(100, 550, 140, 599.9));
assert.equal(bottomBoard.ctx.targetAt(200, 590).type, 'board');
const finger = setup(rect(100, 520, 140, 560));
assert.equal(finger.ctx.targetAt(200, 605).type, 'rack');
const returned = setup(rect(100, 560, 140, 600.1));
returned.ctx.endDrag({ clientX:200, clientY:580 });
assert.equal(returned.ctx.board[14][5], null);
assert.deepEqual(returned.ctx.racks[0], ['A']);
assert.equal(returned.ctx.pending.length, 0);
assert.equal(returned.renders(), 1);
assert.deepEqual(returned.feedback, ["return"]);
const placed = setup(rect(100, 550, 140, 599.9));
placed.ctx.endDrag({ clientX:200, clientY:590 });
assert.deepEqual(placed.feedback, ["tile"]);
const reorder = setup(rect(100, 610, 140, 650));
reorder.ctx.drag.origin = { type:'rack', index:0 };
reorder.ctx.endDrag({ clientX:200, clientY:640 });
assert.deepEqual(reorder.reordered(), [0,2]);
const swap = setup(rect(100, 610, 140, 650)); swap.ctx.swapMode = true;
assert.equal(swap.ctx.targetAt(200, 520).type, 'swap');
assert.equal(swap.ctx.targetAt(200, 640), null);
console.log('PASS: tiny rack overlap on all edges, finger entry, bottom board targeting, actual pending-tile return, rack reorder, and swap targeting.');
