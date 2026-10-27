# Scrobble 1.0.53

Branch: `fix/current-scrobble-board`
Workflow: **Yay Everybody iOS Release**

Adds Clear Spaghetti Sauce and Ceiling Carpet alongside Mirrors. After a saved
player word, choose a fictional sponsor randomly, excluding the previous sponsor.
Remember the last sponsor across app launches where local storage is available.
All artwork is bundled offline. The existing X still returns to Games.

Approved art:
- Clear Spaghetti Sauce: Sponsored by; You can’t see it!
- Ceiling Carpet: Sponsored by; Shut up. *You’re* stupid. (single-line footer)
- Mirrors: existing creative retained.

The previous 1.0.52 submission is awaiting review per the user. This prepares a
separate 1.0.53 build and does not alter or cancel that submission. Start a build
on the branch above in Codemagic. Native TestFlight verification remains pending.

Checks: tests/mirrors-ad.cjs exercises all three creatives, 60 rotations without
consecutive repeats, persistence across launches, saved-turn gating, close/focus,
and navigation cancellation. scripts/verify-current-source.py checks the current
web pipeline and JS syntax, including the sponsor module.

## Opponent last-move name fix

Fixes the reported ShortFuse game showing “Zorro PASSED.” The popup previously
borrowed the opponent name from old board DOM while the next game was loading.
It now uses that game's player profile, or the move's saved name, or “Opponent”
if neither exists. Restored score summaries also prefer the loaded profile.
The regression test covers play/pass/swap and both player positions. Existing
board-generation guards still cancel delayed notices when leaving a game.
