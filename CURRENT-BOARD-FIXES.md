# Current Scrobble board fixes

Baseline: `integration/scrobble-weird-and-modern-ui-2026-10-11` at `aae16283694a9d2009e58ea493f95615890dbf2f` (the 1.0.50 source). Testing branch: `fix/current-scrobble-board`, iOS version 1.0.52.

The existing current build pipeline, archive, native plugins, notifications, feedback, auth, invitations, Name Dropper, Suffixly, stackable settings, and opening-vowel guarantee are retained. The board patch runs after the current source patches and label normalization.

Changes:
- Scope the score bar and delayed move popups to the loaded game.
- Keep the signed-in player's rack visible, disabled during the opponent's turn.
- Show active rules beneath the action icons, using current names and 16.5px text.
- Refine the existing 4x word spaces: five nearby empty squares, minimum Chebyshev distance 3, shared deterministic turn layouts, stable during placement, and new layouts after plays, swaps, or passes. If a nearly full board cannot fit five while honoring spacing, use the available valid squares.

## Verification

Run `python3 scripts/verify-current-source.py` for all current web-source checks without Xcode. The script creates an isolated build from the current archive, applies the complete web patch pipeline, and runs the existing web verification suites plus the new seeded-layout checks.

The DOM regressions require jsdom. With jsdom installed and available to Node, run:

```
node tests/game-switch.cjs
node tests/quad-chaos.cjs
node tests/current-modes.cjs
```

These cover both rack positions and turn transitions, stale popups and computer work, all eight current rule combinations, exact labels, name validation gating, suffix counts, opening vowels, 4x scoring, spacing/proximity, pending-move stability, turn changes, and saved-state reloads.

Native code signing, TestFlight upload, and the two-iPhone checks in `RELEASE-GATE-IN-APP-INVITES.md` remain required before public release. The existing Codemagic publishing setting uploads the build without automatically submitting an external beta review.
