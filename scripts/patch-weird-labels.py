"""Apply player-facing names without changing persisted game rule IDs."""
from pathlib import Path

root = Path("scrobble-mobile/www")
changes = {
    "index.html": {
        "<strong>Quad Chaos</strong>": "<strong>Crazy Random Bonus Spots</strong>",
        "<strong>Suffix Suffocation</strong>": "<strong>Suffixly</strong>",
    },
    "app-v3140.js": {
        "quad_chaos:'Quad Chaos'": "quad_chaos:'Crazy Random Bonus Spots'",
        "suffix_suffocation:'Suffix Suffocation'": "suffix_suffocation:'Suffixly'",
    },
}
for name, replacements in changes.items():
    path = root / name
    source = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        if old not in source and new not in source:
            raise SystemExit(f"Expected label not found in {path}: {old}")
        source = source.replace(old, new)
    path.write_text(source, encoding="utf-8")
print("Applied Make It Weird display names; rule identifiers preserved.")
