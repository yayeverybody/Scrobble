"""Replace Suffixly in new-game setup with the 20-point vowel variation."""
from pathlib import Path

def once(text,old,new):
    if text.count(old)!=1:raise SystemExit('Vowel patch target mismatch: '+old[:90])
    return text.replace(old,new,1)

engine=Path('www/game-engine-v3140.js');game=engine.read_text()
if "hasWeirdRule('vowels_are_worth_too_much')" not in game:
    game=once(game,'function tileValue(letter){',"function tileValue(letter){if(hasWeirdRule('vowels_are_worth_too_much')&&['A','E','I','O','U'].includes(letter))return 20;")
    game=once(game,"const names={", "const names={vowels_are_worth_too_much:'Vowels Are Worth Too Much',")
    engine.write_text(game)
app=Path('www/app-v3140.js');js=app.read_text()
if "vowels_are_worth_too_much:'Vowels Are Worth Too Much'" not in js:
    js=once(js,'const WEIRD_LABELS={',"const WEIRD_LABELS={vowels_are_worth_too_much:'Vowels Are Worth Too Much',")
    app.write_text(js)
index=Path('www/index.html');html=index.read_text()
if 'value="vowels_are_worth_too_much"' not in html:
    html=once(html,'<label class="weirdChoice"><input type="checkbox" value="suffix_suffocation"><span><strong>Suffixly</strong><small>Add 4 S, 3 D, 3 R and 2 Y tiles.</small></span></label>', '<label class="weirdChoice"><input type="checkbox" value="vowels_are_worth_too_much"><span><strong>Vowels Are Worth Too Much</strong><small>A, E, I, O and U are worth 20 points each.</small></span></label>')
    index.write_text(html)
print('PASS: new-game Suffixly replaced by Vowels Are Worth Too Much; existing games retain their saved rules')
