"""Fail the build rather than ship a stale Scrobble game bundle.

The checked-in Capacitor ZIP is an older build with five legacy exclusive modes.
Changing display strings alone cannot implement new game rules.
"""
from pathlib import Path

root = Path("scrobble-mobile/www")
html = (root / "index.html").read_text(encoding="utf-8")
app = (root / "app-v3140.js").read_text(encoding="utf-8")
engine = (root / "game-engine-v3140.js").read_text(encoding="utf-8")
required = {
    "three new mode IDs in setup": all(f'value="{x}"' in html for x in ("quad_chaos", "name_dropper", "suffix_suffocation")),
    "new mode implementation in engine": all(x in engine for x in ("quad_chaos", "name_dropper", "suffix_suffocation")),
    "stackable mode selection": "other.checked=false" not in app,
}
failed = [name for name, passed in required.items() if not passed]
if failed:
    raise SystemExit(
        "STALE SCROBBLE GAME BUNDLE: " + "; ".join(failed)
        + ". Replace Scrobble_Mobile_0_1_Capacitor.zip with the actual updated game "
          "source before building. Refusing to publish a misleading TestFlight build."
    )
print("Scrobble game bundle passed feature/source checks.")
