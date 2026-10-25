# Mirrors fictional sponsor

`mirrors.jpg` is original artwork generated with the built-in image generation tool,
then edited with that tool to add the finished lettering. Converted to JPEG for
bundling in the app. No external advertising SDK, tracking, links, purchases or
network requests. Copy is also available as accessible HTML in mirrors-ad.html.

Final creative prompt: Preserve the funny mirror photo, man, delighted expression,
reflection and warm colors. Add a cream header with small SPONSORED BY, enormous
retro dark-brown serif Mirrors., and the exact tagline Reflect yourself back to
yourself. Add a cream footer reading Now featuring: you. Use generous margins and
polished 1970s print-ad styling, no phone frame or raster UI controls.

After a player word is saved, wait 1.6 seconds for score feedback, then show the
ad. Passes, swaps, CPU plays and failed saves do not trigger it. Navigation resets
pending ads; polling the same game does not. Close X returns to Games through the
existing home flow. Computer responses pause while the ad is visible and resume
when that game is reopened. Native TestFlight layout verification is pending.

Validation: NODE_PATH=<jsdom modules> node tests/mirrors-ad.cjs;
python3 scripts/verify-current-source.py.
