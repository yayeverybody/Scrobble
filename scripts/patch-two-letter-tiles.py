"""Install the Two-Letter Tiles rule in the generated mobile sources."""
from pathlib import Path


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'Expected one matching source fragment: {old[:100]}')
    return source.replace(old, new, 1)


web = Path('www')
for filename in ('app-v3140.js', 'game-engine-v3140.js'):
    path = web / filename
    path.write_text(replace_once(path.read_text(),
        "hidden_land_mines:'Hidden Land Mines',",
        "two_letter_tiles:'Two-Letter Tiles',hidden_land_mines:'Hidden Land Mines',"))

html = web / 'index.html'
choice = '      <label class="weirdChoice"><input type="checkbox" value="hidden_land_mines">'
html.write_text(replace_once(html.read_text(), choice,
    '      <label class="weirdChoice"><input type="checkbox" value="two_letter_tiles"><span>'
    '<strong>Two-Letter Tiles</strong><small>Three each of SH, CH and TH. Each tile is worth 15 points.</small>'
    '</span></label>\n' + choice))

path = web / 'game-engine-v3140.js'
engine = path.read_text()
engine = replace_once(engine, 'function tileValue(letter){', """const twoLetterTiles=['SH','CH','TH'];
function tileValue(letter){if(twoLetterTiles.includes(letter))return 15;""")
engine = replace_once(engine, '<text x="40" y="84" text-anchor="middle" font-family="Arial" font-size="76"',
    '<text x="${letter.length===2?50:40}" y="${letter.length===2?76:84}" text-anchor="middle" '
    'font-family="Arial" font-size="${letter.length===2?48:76}"')
engine = replace_once(engine, 'const counts={A:20,L:9,O:18,R:14,N:11,E:30};',
    'const counts={A:20,L:9,O:18,R:14,N:11,E:30};\n    addTwoLetterTiles(counts);')
engine = replace_once(engine, '  const a=[];\n  Object.entries(counts)', '  addTwoLetterTiles(counts);\n  const a=[];\n  Object.entries(counts)')
engine = replace_once(engine, 'function makeBag(){', """function addTwoLetterTiles(counts){
  if(hasWeirdRule('two_letter_tiles')){
    for(const tile of twoLetterTiles)counts[tile]=3;
  }
}
function makeBag(){""")

# A two-letter tile forms a cross-word only if there is an adjacent tile.
engine = replace_once(engine, 'w.word.length>1&&!seen.has(k)', 'w.cells.length>1&&!seen.has(k)')
engine = replace_once(engine, 'if(word.length===1)return{valid:true,score:0,word:null};',
    'if(!pre&&!post)return{valid:true,score:0,word:null};')

start = engine.index('function cpuEvaluatePlacement(')
end = engine.index('function cpuChooseMove(', start)
cpu = engine[start:end]
cpu = replace_once(cpu, 'function cpuEvaluatePlacement(word,r,c,dr,dc,rackCounts){',
    'function cpuEvaluatePlacement(tiles,r,c,dr,dc,rackCounts){')
evaluation, _ = cpu.split('function cpuFindMoves(){', 1)
evaluation = evaluation.replace('word.length', 'tiles.length').replace('ch=word[i]', 'ch=tiles[i]')
evaluation = replace_once(evaluation, 'return{word,r,c,dr,dc,', "return{word:tiles.join(''),r,c,dr,dc,")
engine = engine[:start] + evaluation + Path(__file__).with_name('two-letter-cpu.js').read_text() + engine[end:]

path.write_text(engine)
