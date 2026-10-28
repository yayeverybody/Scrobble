# Scrobble 1.0.55

Branch: `fix/current-scrobble-board`
Workflow: **Yay Everybody iOS Release** (`scrobble-ios-release`)

Adds three approved ads to the existing seven:

- High Cut Jean Shorts — Mobility Unmatched.
- Dalton’s Splashless Chili — no footer; final three-cylinder scene.
- Invest in Glass — TURN GOLD INTO GLASS in shiny gold block capitals; no Sponsored By.

Retains Mirrors, Clear Spaghetti Sauce, Ceiling Carpet, Soft-Sided Coffee Mugs, Nelson’s Business Suits, Dr. Small’s Prescription Windshields, and Neon Green, plus all current board fixes. Disposable Ties is excluded.

All ten ads are bundled offline, rotate without consecutive repeats, and remember the previous ad across launches. Existing saved-turn gating and close-to-Games behavior are unchanged.

Validation: `tests/mirrors-ad.cjs` checks ten creatives, 120 rotations, final accessible copy, bundled files, persisted selection, close/focus and turn/navigation gating. `scripts/verify-current-source.py` checks the web build pipeline and JavaScript syntax. Native signed build and device verification remain separate checks.

This is an internal testing build. Public App Store submission is not requested.
