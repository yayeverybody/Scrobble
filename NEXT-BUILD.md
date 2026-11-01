# Scrobble 1.0.60

Branch: `feature/hidden-land-mines`
Workflow: **Yay Everybody iOS Release** (`scrobble-ios-release`)

Replaces Name Dropper in new-game setup with Hidden Land Mines. Ten randomly assigned, fixed traps have a minimum straight-line distance of five board spaces, including diagonals. A valid move hitting a trap stays on the board and its total score (including crosswords and bonuses) is deducted once. Multiple traps on one move do not multiply the penalty. Scores may be negative. Detonated squares remain dark red and cannot explode again. Both players receive an explanation with a large 💥 icon, an explosion sound, and a maximum-intensity 0.75-second rumble with repeated sharp impacts. Existing sound and haptic settings are respected.

Computer games store their mines with the saved game; the AI search does not inspect them. Multiplayer mines stay in a private server table, resolve when a move is accepted, and are never sent to clients before detonation. Rematches receive new traps. Existing Name Dropper games retain their original rules.

Backend migration has been applied and tested. iOS build and physical-device sound/visual QA remain for the next release. No App Store submission was started. Retains the prior sponsor artwork and October 31 move-highlight / computer-ad-return fixes.

Validation: tests/land-mines.cjs, tests/land-mines.sql, all eight Weird combinations, board switching, Quad Chaos, move-coordinate highlights, own/opponent notices, score feedback, existing release web checks. SQL fixtures roll back automatically.

Suggested What’s New: New Make It Weird option: Hidden Land Mines. Five secret board spaces can turn your big score into a deduction. Watch your step.

Audio follow-up: compressed and normalized the explosion sample and gave it a dedicated 55% playback level on both native iOS and web fallback. Other effects retain their previous levels. Packaging and signal checks now require the explosion, including after Capacitor sync.

Mine notices remain until OK or a backdrop tap. Cloud refreshes retain the open notice; sponsors and computer turns wait for dismissal. Existing games retain their saved mine layout; ten mines apply to new games.
