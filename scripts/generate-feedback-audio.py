"""Install bundled, licensed Kenney samples. No synthesis or build-time downloads."""
from pathlib import Path
import shutil

def generate(directory):
    directory.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_name('feedback-assets')
    for file in source.iterdir():
        shutil.copyfile(file, directory / file.name)
    expected = ['finish', 'big-finish', 'button', 'return', 'shuffle', 'error', 'create'] + [f'tile-{i}' for i in range(3)] + [f'note-{i}' for i in range(12)]
    for name in expected:
        assert (directory / (name + '.wav')).read_bytes()[:4] == b'RIFF', name

if __name__ == '__main__':
    generate(Path('www/feedback'))
