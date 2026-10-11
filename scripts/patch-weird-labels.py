"""Verify bundled game features, rename modes, and mark this test build."""
from pathlib import Path

root = Path("scrobble-mobile/www")
index = root / "index.html"
app_path = root / "app-v3140.js"
engine_path = root / "game-engine-v3140.js"
html = index.read_text(encoding="utf-8")
app = app_path.read_text(encoding="utf-8")
engine = engine_path.read_text(encoding="utf-8")

ids = ("quad_chaos", "name_dropper", "suffix_suffocation")
checks = {
    "new setup toggles": all(f'value="{rule}"' in html for rule in ids),
    "new engine rule handlers": all(rule in engine for rule in ids),
    "multi-select setup": "Optional. Mix and match." in html,
    "correct JavaScript loaded": 'src="app-v3140.js"' in html and 'src="game-engine-v3140.js"' in html,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Invalid Scrobble game archive: " + ", ".join(failed))

html = html.replace("<strong>Quad Chaos</strong>", "<strong>Crazy Random Bonus Spots</strong>")
html = html.replace("<strong>Suffix Suffocation</strong>", "<strong>Suffixly</strong>")
app = app.replace("quad_chaos:'Quad Chaos'", "quad_chaos:'Crazy Random Bonus Spots'")
app = app.replace("suffix_suffocation:'Suffix Suffocation'", "suffix_suffocation:'Suffixly'")
# Visible diagnostic distinguishes a new native bundle from stale installed content.
html = html.replace('<h2 id="gameModeTitle">New Game</h2>', '<h2 id="gameModeTitle">New Game</h2><div style="text-align:center;color:#cce9ff;font-size:12px;margin-top:-5px;margin-bottom:10px">Make It Weird test • 1.0.47</div>')
if "<strong>Crazy Random Bonus Spots</strong>" not in html or "<strong>Suffixly</strong>" not in html:
    raise SystemExit("Make It Weird display labels were not applied")
index.write_text(html, encoding="utf-8")
app_path.write_text(app, encoding="utf-8")
print("Verified bundled rules and applied Make It Weird 1.0.47 test marker.")
