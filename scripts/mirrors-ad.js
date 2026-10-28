/* A fictional sponsor. Bundled artwork; no network, tracking or purchases. */
(() => {
  'use strict';
  const overlay = document.getElementById('mirrorsAd');
  const close = document.getElementById('mirrorsAdClose');
  const roster = [
    {id:'mirrors', title:'Mirrors.', tagline:'Reflect yourself back to yourself.', footer:'Now featuring: you.', alt:'A delighted goof gazes adoringly at his own reflection in an ornate mirror.'},
    {id:'clear-spaghetti-sauce', title:'Clear Spaghetti Sauce', tagline:'You can’t see it!', footer:'', alt:'A kid eats a huge bowl of spaghetti and meatballs beside a jar of transparent spaghetti sauce.'},
    {id:'ceiling-carpet', title:'Ceiling Carpet', tagline:'Shut up. You’re stupid.', footer:'', alt:'An installer on a stepladder vacuums a living room ceiling covered in beige carpet.'},
    {id:'soft-sided-coffee-mugs', title:'Soft-Sided Coffee Mugs', tagline:'Finally. A softer cup of coffee.', footer:'Better drink it quick.', alt:'A woman presents quilted fabric coffee mugs that leak coffee through their seams.'},
    {id:'nelsons-business-suits', title:'Nelson’s Business Suits', tagline:'', footer:'Fine tailoring. All-day comfort. Insulated gravy pocket.', alt:'A businessman on a bus pours gravy from his suit pocket onto mashed potatoes in his palm.'},
    {id:'neon-green', title:'Neon Green', tagline:'', footer:'From the makers of Reflective Orange.', alt:'An 1980s family dressed in neon green poses in a neon green living room with hot pink lampshades.'},
    {id:'prescription-windshields', title:'Dr. Small’s Prescription Windshields', tagline:'', footer:'Throw away your eyeglasses.', alt:'A normal blue sedan with a prescription windshield that magnifies and distorts the driver’s face and surrounding interior like a fisheye lens.'},
    {id:'high-cut-jean-shorts', title:'High Cut Jean Shorts', tagline:'', footer:'Mobility Unmatched', alt:'A man in high-cut denim shorts poses beside a lawnmower on a suburban lawn.'},
    {id:'splashless-chili', title:'Dalton’s Splashless Chili', tagline:'', footer:'', alt:'A man drops a solid can-shaped cylinder of chili toward a bowl. Another cylinder rests across the bowl edge and a third lies on the counter.'},
    {id:'invest-in-glass', title:'Invest in Glass', tagline:'', footer:'TURN GOLD INTO GLASS', alt:'A banker proudly displays stacks of ordinary glass panes in front of a vault. Turn gold into glass appears in shiny gold block lettering.'}
  ];
  const lastAdKey = 'scrobble-last-fictional-sponsor';
  let lastAd;
  try { lastAd = localStorage.getItem(lastAdKey); } catch (_) {}
  function chooseAd() {
    const candidates = roster.filter(ad => ad.id !== lastAd);
    const ad = candidates[Math.floor(Math.random() * candidates.length)];
    lastAd = ad.id;
    try { localStorage.setItem(lastAdKey, ad.id); } catch (_) {}
    document.getElementById('mirrorsAdTitle').textContent = ad.title;
    document.getElementById('mirrorsAdTagline').textContent = ad.tagline;
    overlay.querySelector('.mirrorFooter').textContent = ad.footer;
    const artwork = document.getElementById('fakeAdArtwork');
    artwork.src = 'fake-ads/' + ad.id + '.jpg';
    artwork.alt = ad.alt;
    overlay.dataset.sponsor = ad.id;
  }
  let viewToken = 0, pendingAd;
  function dismiss() {
    if (overlay.hidden) return;
    overlay.hidden = true;
    document.body.classList.remove('scrobbleAdActive');
    window.dispatchEvent(new CustomEvent('scrobble:home'));
    document.querySelector('#newGameDash')?.focus();
  }
  window.ScrobbleFakeAd = {
    get viewToken() { return viewToken; },
    reset() {
      viewToken++;
      clearTimeout(pendingAd);
      overlay.hidden = true;
      document.body.classList.remove('scrobbleAdActive');
    },
    afterTurn(token) {
      clearTimeout(pendingAd);
      pendingAd = setTimeout(() => {
        if (token === viewToken) window.ScrobbleFakeAd.show();
      }, 1600);
    },
    show() {
      if (!document.body.classList.contains('scrobbleGameActive') || !overlay.hidden) return;
      chooseAd();
      overlay.hidden = false;
      document.body.classList.add('scrobbleAdActive');
      close.focus();
    }
  };
  close.addEventListener('click', dismiss);
  overlay.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); dismiss(); }
    if (event.key === 'Tab') { event.preventDefault(); close.focus(); }
  });
  // Home navigation also dismisses the fictional sponsor.
  window.addEventListener('scrobble:home', () => {
    overlay.hidden = true;
    document.body.classList.remove('scrobbleAdActive');
  });
})();
