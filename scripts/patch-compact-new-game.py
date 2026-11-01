"""Compact the two setup flows without changing game handlers or rule titles."""
from pathlib import Path
p=Path('www/index.html');html=p.read_text()
updates={
 'Five moving 4× word spaces appear each turn.':'Five moving 4× word spaces each turn.',
 'Ten hidden traps. Hit one and your move’s points are deducted. The word stays.':'Ten hidden traps. Hit one: lose the move’s points. Your word stays.',
 'A, E, I, O and U are worth 20 points each.':'Vowels are worth 20 points each.',
}
for old,new in updates.items():
 assert html.count(old)==1,'Setup copy target changed: '+old
 html=html.replace(old,new,1)
assert html.count('</head>')==1
css=Path(__file__).with_name('compact-new-game.css').read_text()
html=html.replace('</head>','<style id="scrobble-compact-new-game">'+css+'</style></head>')
p.write_text(html)
print('PASS: compact friend/computer setup and safe-area bounds installed')
