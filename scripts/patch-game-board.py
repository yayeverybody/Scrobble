"""Recent board fixes, applied to the verified modern integration source."""
from pathlib import Path
import re
scripts = Path(__file__).resolve().parent
engine = Path('www/game-engine-v3140.js')
app = Path('www/app-v3140.js')
index = Path('www/index.html')
game, js, html = engine.read_text(), app.read_text(), index.read_text()

def once(source, old, new):
    if source.count(old) != 1:
        raise SystemExit('Board patch expected one target: ' + old[:100])
    return source.replace(old, new, 1)

if 'function clearBoardPresentation()' not in game:
    # Require the current rule system and modern build, not the old main archive.
    for marker in ["function seededQuadSquares()", "if(hasWeirdRule('name_dropper')", "if(hasWeirdRule('suffix_suffocation'))", 'finishComputerPassStalemate', 'ensureOpeningVowels']:
        if marker not in game: raise SystemExit('Current release prerequisite missing: ' + marker)
    for marker in ['id="playComputerMode"', 'id="friendModePanel"', 'id="sharedWeirdBox"']:
        if marker not in html: raise SystemExit('Current setup prerequisite missing: ' + marker)
    game = once(game, 'function hasWeirdRule(id)', (scripts/'game-board-helpers.js').read_text()+'\nfunction hasWeirdRule(id)')
    game = once(game, 'function freshLocalGame(){', "function freshLocalGame(){clearBoardPresentation();cloudRackMode=false;spectatorMode=false;quadContext='local-'+Date.now()+'-'+Math.random();quadTurnNumber=0;")
    game = once(game, "loadComputerState(s,difficulty='medium'){", "loadComputerState(s,difficulty='medium'){clearBoardPresentation();cloudRackMode=false;quadContext=s.quadContext||'local';quadTurnNumber=s.quadTurnNumber||0;")
    game = once(game, 'loadCloudState(s,slot){', "loadCloudState(s,slot){clearBoardPresentation();cloudRackMode=true;quadContext=String(s.id||'cloud')+'|'+String(s.updated_at||'');quadTurnNumber=0;")
    game = once(game, 'function render(){refreshQuadSpaces();', 'function render(){if(cloudRackMode&&current!==viewRackIndex)spectatorMode=true;refreshQuadSpaces();')
    game = once(game, 'const rackOwner=cpuMode?0:(spectatorMode?viewRackIndex:current);', 'const rackOwner=cpuMode?0:((cloudRackMode||spectatorMode)?viewRackIndex:current);')
    game = once(game, 'render=function(){originalRender();', 'render=function(){originalRender();renderBoardDetails();')
    game = once(game, '  showTurnNotice(summary){showTurnNotice(summary)},', '  showTurnNotice(summary){showTurnNotice(summary)},\n  scheduleTask(callback,delay){return scheduleBoardTask(callback,delay)},\n  leaveGame(){cpuGeneration++;cpuThinking=false;clearBoardPresentation()},')
    game = game.replace('setTimeout(()=>showTurnNotice(lastMoveSummary),120)', 'scheduleBoardTask(()=>showTurnNotice(lastMoveSummary),120)')
    game = once(game, 'setTimeout(()=>animateLastMove(summary),80)', 'scheduleBoardTask(()=>animateLastMove(summary),80)')
    # Scope the delayed zoom-out from a dismissed move notice too.
    start, end = game.index('function animateLastMove('), game.index('function hideTurnNotice(')
    game = game[:start]+game[start:end].replace('setTimeout(', 'scheduleBoardTask(')+game[end:]
    game = once(game, 'async function playMove(){', 'async function playMove(){\n  const generation=boardViewGeneration;')
    game = once(game, 'for(const w of words)results.push(await realDictionaryLookup(w.word));', 'for(const w of words){results.push(await realDictionaryLookup(w.word));if(generation!==boardViewGeneration)return;}')
    # Enrich the restored move from this game's profiles rather than stale DOM names.
    start=game.index('loadCloudState(s,slot){')
    tail=once(game[start:], 'lastMoveSummary=s.lastMoveSummary||null;', "lastMoveSummary=s.lastMoveSummary?{...s.lastMoveSummary,playerName:s.lastMoveSummary.playerName||s['player'+(s.lastMoveSummary.playedBy+1)+'_profile']?.display_name}:null;")
    game=game[:start]+tail
    # Reuse current Quad Chaos rendering/scoring; refine only its turn key and placement.
    game = once(game, 'function quadTurnIdentity(){return `', 'function quadTurnIdentity(){return `${quadContext}:${quadTurnNumber}:')
    game = once(game, 'function quadDeterministicKey(){return `', 'function quadDeterministicKey(){return `${quadContext}:${quadTurnNumber}:')
    start,end=game.index('function seededQuadSquares(){'),game.index('function refreshQuadSpaces(')
    game=game[:start]+(scripts/'quad-space-placement.js').read_text()+game[end:]
    game = game.replace('current=1-current;', 'current=1-current;quadTurnNumber++;')
    game = once(game, 'shuffle(bag);current=0;cpuThinking=false;', 'shuffle(bag);current=0;quadTurnNumber++;cpuThinking=false;')
    game = once(game, 'current=0;cpuThinking=false;refreshQuadSpaces(true);lastMoveSummary=', 'current=0;quadTurnNumber++;cpuThinking=false;refreshQuadSpaces(true);lastMoveSummary=')
    game = game.replace('weirdRules,quadSpaces,quadTurnKey,', 'weirdRules,quadSpaces,quadTurnKey,quadContext,quadTurnNumber,')
    game = once(game, 'if(!s)return false;', "if(!s)return false;quadContext=s.quadContext||'local';quadTurnNumber=s.quadTurnNumber||0;")
    # Old saved layouts must be re-evaluated using the new identity and spacing.
    game = game.replace('quadTurnKey=s.quadTurnKey||null;', 'quadTurnKey=null;')
    game = game.replace('quadTurnKey=s.quad_turn_key||null;', 'quadTurnKey=null;')

    js = once(js, '  function showDash(){', '  function showDash(){\n    window.ScrobbleGame.leaveGame();')
    for old in ['setTimeout(()=>window.ScrobbleGame.showTurnNotice(rec.state.lastMoveSummary),180)', 'setTimeout(()=>window.ScrobbleGame.showTurnNotice(summary),180)', 'setTimeout(()=>{if(currentComputer&&loadComputerRecord()?.id===rec.id)window.ScrobbleGame.runComputerTurn(rec.difficulty)},350)', 'setTimeout(()=>{if(currentComputer&&loadComputerRecord()?.id===rec.id)window.ScrobbleGame.runComputerTurn(rec.difficulty)},6000)']:
        js = once(js, old, old.replace('setTimeout(', 'window.ScrobbleGame.scheduleTask('))
    html = once(html, '<script src="last-play-v3120.js?v=312"></script>', '')
    html = once(html, '</span></button></div></section>\n</div>', '</span></button></div><div id="activeWeirdRules" class="activeWeirdRules" hidden></div></section>\n</div>')
    html = once(html, '</head>', '''<style id="current-game-rule-label">
#scrobble-v4 .activeWeirdRules{background:#0b69a9;padding:7px 10px;text-align:center;color:#d9efff;font:600 16.5px/1.35 Arial,Helvetica,sans-serif;overflow-wrap:anywhere}
#scrobble-v4 .activeWeirdRules[hidden]{display:none}
</style></head>''')
    engine.write_text(game);app.write_text(js);index.write_text(html)
print('PASS: board fixes applied to the modern integration, preserving all three stackable modes')

# Paint the waiting rack directly. Nested filters on percentage-sized SVG tiles
# can disappear in WKWebView even when the rack DOM and saved data are intact.
game=engine.read_text()
if 'owner=startingPlayer,muted=false' not in game:
    game=once(game, 'function tileSVG(letter,owner=startingPlayer){', 'function tileSVG(letter,owner=startingPlayer,muted=false){')
    game=once(game, "gid='g'+letter+value+(opponent?'o':'s')", "gid='g'+letter+value+(opponent?'o':'s')+(muted?'m':'')")
    for old,new in [
        ("top=opponent?'#ffeebc':'#ffdc79'", "top=muted?'#e0e9ef':opponent?'#ffeebc':'#ffdc79'"),
        ("middle=opponent?'#ffe3a4':'#ffc748'", "middle=muted?'#bccedb':opponent?'#ffe3a4':'#ffc748'"),
        ("bottom=opponent?'#f6d08f':'#eda01f'", "bottom=muted?'#9bb3c5':opponent?'#f6d08f':'#eda01f'"),
        ("stroke=opponent?'#eac589':'#d58b12'", "stroke=muted?'#7893a8':opponent?'#eac589':'#d58b12'"),
        ("ink='#111'", "ink=muted?'#344b5c':'#111'"),
        ('tileSVG(l,rackOwner)', 'tileSVG(l,rackOwner,spectatorMode||(cpuMode&&current===1))')
    ]:
        game=once(game,old,new)
    engine.write_text(game)
html=index.read_text()
if 'id="waiting-rack-paint"' not in html:
    html=once(html,'</head>','''<style id="waiting-rack-paint">
#scrobble-v4.spectator #rack .rackTile{filter:none!important;opacity:1!important;transform:none!important}
#scrobble-v4 #rack .tileGraphic{filter:none!important}
#scrobble-v4 #rack .rackTile{aspect-ratio:1/1}
</style></head>''')
    index.write_text(html)
