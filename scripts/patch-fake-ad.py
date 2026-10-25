"""Show a fictional sponsor after a committed player word; X returns to games."""
from pathlib import Path
import shutil
scripts=Path(__file__).resolve().parent
app=Path('www/app-v3140.js');html=Path('www/index.html')
s=app.read_text()
if 'ScrobbleFakeAd' not in s:
    start=s.index("  window.addEventListener('scrobble:turn-ended',async e=>{")
    end=s.index("  window.addEventListener('scrobble:challenge-created'",start)
    block=s[start:end]
    block=block.replace("async e=>{", "async e=>{\n    const sponsorView=window.ScrobbleFakeAd?.viewToken;",1)
    old='      saveCurrentComputerGame();'
    assert block.count(old)==1
    block=block.replace(old,old+"\n      if(e.detail?.move_type==='play'&&e.detail?.playedBy===0&&sponsorView===window.ScrobbleFakeAd?.viewToken)window.ScrobbleFakeAd?.afterTurn(sponsorView);")
    old="      statusEl.textContent='Cloud connected • '+(accountDisplayName(user)||profileLabel(myProfile,'Player'))"
    assert block.count(old)==1
    block=block.replace(old,old+";\n      if(e.detail?.move_type==='play'&&sponsorView===window.ScrobbleFakeAd?.viewToken)window.ScrobbleFakeAd?.afterTurn(sponsorView)")
    block=block.replace('if(currentComputer&&loadComputerRecord()?.id===rec.id)', "if(currentComputer&&!document.body.classList.contains('scrobbleAdActive')&&loadComputerRecord()?.id===rec.id)")
    s=s[:start]+block+s[end:]
    for name in ['showGame','showDash']:
        old='  function '+name+'(){'
        assert s.count(old)==1
        s=s.replace(old,old+'\n    window.ScrobbleFakeAd?.reset();')
    app.write_text(s)
h=html.read_text()
if 'id="mirrorsAd"' not in h:
    h=h.replace('</body>',(scripts/'mirrors-ad.html').read_text()+'\n</body>')
    html.write_text(h)
shutil.copyfile(scripts/'mirrors-ad.js',Path('www/mirrors-ad.js'))
assets=Path('www/fake-ads');assets.mkdir(exist_ok=True)
shutil.copyfile(scripts/'fake-ad-assets/mirrors.jpg',assets/'mirrors.jpg')
print('PASS: Mirrors ad appears after saved player plays, with explicit close-to-games')
