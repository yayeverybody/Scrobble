"""Original short bell tones; deterministic PCM assets, no downloads or dependencies."""
from pathlib import Path
import math
import struct
import wave

def generate(directory):
    directory.mkdir(parents=True, exist_ok=True)
    rate = 22050
    # Pentatonic rise avoids dissonance when short notes overlap.
    notes = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24, 26]
    for name, tones, duration in [(f'note-{i}', [(0, 330 * 2 ** (n / 12))], .12) for i, n in enumerate(notes)] + [('finish', [(0, 660), (.07, 830.61), (.14, 990)], .48)]:
        samples = []
        for i in range(int(rate * duration)):
            t = i / rate
            value = 0
            for onset, frequency in tones:
                age = t - onset
                if age < 0:
                    continue
                envelope = min(1, age / .006) * math.exp(-age * 18)
                # Rounded fundamental with a very quiet bell harmonic.
                value += envelope * (math.sin(2 * math.pi * frequency * age) + .12 * math.sin(2 * math.pi * frequency * 2 * age)) * .24
            value *= min(1, (duration - t) / .015)
            samples.append(struct.pack('<h', int(max(-1, min(1, value)) * 32767)))
        with wave.open(str(directory / f'{name}.wav'), 'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate); f.writeframes(b''.join(samples))

if __name__ == '__main__':
    generate(Path('www/feedback'))
