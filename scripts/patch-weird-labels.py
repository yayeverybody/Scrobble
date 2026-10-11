"""Verify and label the bundled Scrobble Make It Weird implementation.

Fail closed if the Capacitor archive is stale or has unexpected source.
"""
from pathlib import Path

root = Path("scrobble-mobile/www")
html_path = root / "index.html"
app_path = root / "app-v3140.js"
engine_path = root / "game-engine-v3140.js"
html = html_path.read_text(encoding="utf-8")
app = app_path.read_text(encoding="utf-8")
engine = engine_path.read_text(encoding="utf-8")

checks = {
    "three new options": all(f'value="{rule}"' in html for rule in ("quad_chaos", "name_dropper", "suffix_suffocation")),
    "mix and match": "Optional. Mix and match." in html,
    "selected rules": "function selectedWeirdRules()" in app,
    "floating bonus implementation": all(s in engine for s in ("seededQuadSquares()", "squareBonus(r,c)", "b==='qw'")),
    "suffix distribution": "Object.entries({S:4,D:3,R:3,Y:2})" in engine,
    "proper-noun review": "pendingChallengeConfirm" in engine and "name_dropper" in engine,
}
failed = [k for k,v in checks.items() if not v]
if failed:
    raise SystemExit("Scrobble bundle feature check failed: " + ", ".join(failed))

for old,new in (
    ("<strong>Quad Chaos</strong>", "<strong>Crazy Random Bonus Spots</strong>"),
    ("<strong>Suffix Suffocation</strong>", "<strong>Suffixly</strong>"),
):
    if old not in html and new not in html:
        raise SystemExit("Missing setup label " + old)
    html = html.replace(old,new)
for old,new in (
    ("quad_chaos:'Quad Chaos'", "quad_chaos:'Crazy Random Bonus Spots'"),
    ("suffix_suffocation:'Suffix Suffocation'", "suffix_suffocation:'Suffixly'"),
):
    if old not in app and new not in app:
        raise SystemExit("Missing app label " + old)
    app = app.replace(old,new)

# Permanent diagnostic for this development build, independent of game mode modal layout.
marker = '<div id="scrobble-build-id" style="position:fixed;bottom:0;right:0;z-index:2147483647;background:#13283a;color:white;padding:3px 7px;font:11px Arial;pointer-events:none">WEIRD TEST 1.0.48</div>'
if 'id="scrobble-build-id"' not in html:
    if '</body>' not in html:
        raise SystemExit("No closing body tag for build marker")
    html = html.replace('</body>', marker + '\\n</body>', 1)
if "WEIRD TEST 1.0.48" not in html:
    raise SystemExit("Missing build marker")
html_path.write_text(html, encoding="utf-8")
app_path.write_text(app, encoding="utf-8")
print("PASS: bundled game contains three stackable modes and existing gameplay handlers.")
