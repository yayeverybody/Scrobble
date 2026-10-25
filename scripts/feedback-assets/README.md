# Scrobble sampled sound effects

Source: Kenney Impact Sounds 1.0 (2019), https://kenney.nl/assets/impact-sounds
and Kenney Interface Sounds 1.0 (2020), https://kenney.nl/assets/interface-sounds.
Both packs are CC0; original license notices are included alongside the samples.
Downloaded from the creator's packs on 2026-10-25. No paid service or runtime download.

`manifest.json` maps each output to the source file and pitch adjustment.
Effects converted with FFmpeg to mono 16-bit PCM WAV, 22050 Hz, cropped to short
one-shots with a 25 ms end fade and a peak limiter at 0.85. Note variants are
pitch-shifted samples of select_001, not oscillator-generated tones.

Tile placement cycles three wood clacks; return uses a medium wood tap; shuffle
and swap use switch_006; invalid moves use a heavy wood thunk; buttons use a soft
click. Score animation uses quiet sample ticks and finishes with confirmation_002,
or confirmation_004 for gains of at least 50 points and game completion.
Existing volume reduction, independent sound/haptic settings, interruption and
background cancellation remain in place. iPhone listening check is required in
TestFlight before release; desktop checks cannot verify speaker balance or feel.
