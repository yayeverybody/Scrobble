"""Check shipped audio content, duration, format and headroom rather than filenames alone."""
from pathlib import Path
import wave, array, math
root=Path(__file__).resolve().parents[1]/'scripts/feedback-assets'
for file in root.glob('*.wav'):
    with wave.open(str(file)) as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,22050),file
        duration=w.getnframes()/w.getframerate()
        samples=array.array('h',w.readframes(w.getnframes()))
    assert .03<duration<=.81,(file,duration)
    assert 100<max(map(abs,samples))<32700,file
    assert math.sqrt(sum(x*x for x in samples)/len(samples))>10,file
assert len(list(root.glob('*.wav')))==22
assert len({(root/f'tile-{i}.wav').read_bytes() for i in range(3)})==3
print('PASS: all 22 bundled samples have valid PCM, audible signal, short durations, peak headroom and three different wood clacks')
