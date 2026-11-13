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
    {id:'powdered-water', title:'Powdered Water', tagline:'', footer:'ORIGINAL FLAVOR', alt:'A freckled redheaded boy in a striped 1970s shirt pours powdered water into a glass.'},
    {id:'foil-ball', title:'Foil Ball', tagline:'', footer:'ENDLESSLY ENTERTAINING', alt:'A freckled redheaded boy admires a foil ball in a 1970s den beneath shiny silver foil lettering.'},
    {id:'invest-in-glass', title:'Invest in Glass', tagline:'', footer:'TURN GOLD INTO GLASS', alt:'A banker proudly displays stacks of ordinary glass panes in front of a vault. Turn gold into glass appears in shiny gold block lettering.'},
    {id:'border-smoothie', title:'The Border Smoothie', tagline:'', footer:'LEAVE YOUR TEETH AT HOME', alt:'Señor Pronto introduces The Border Smoothie: a savory burrito smoothie in a giant striped cup, with the slogan Leave your teeth at home.'},
    {id:'sea-ferrets', title:'Sea Ferrets', tagline:'', footer:'“THEY’RE YOUR PROBLEM NOW.”', alt:'Vintage comic-book Sea Ferrets advertisement with an underwater ferret family and the quoted slogan They’re your problem now.'}
    ,{id:'edible-aquarium-gravel', title:'Edible Aquarium Gravel', tagline:'', footer:'', alt:'Retro Edible Aquarium Gravel advertisement with a girl eating candy pebbles, a detailed product bag, a bowl of candy and a goldfish aquarium.'}
    ,{id:'extra-wide-straws', title:'Extra Wide Straws', tagline:'', footer:'', alt:'A boy drains a milkshake through an extra-wide straw while a stunned soda jerk holds a stopwatch. A skull and crossbones warns about brain freeze.'}
    ,{id:'bear-roll-on', title:'Bear Roll-On', tagline:'', footer:'', alt:'A camper applies roll-on bear repellent to an upright grizzly looming over him.'}
    ,{id:'gary-glimmer', title:'The Magic of Gary Glimmer', tagline:'', footer:'', alt:'Vintage TV magic special with a levitating assistant and the caption Watch Gary appear from the magic closet.'}
    ,{id:'gaggalher', title:'Gaggalher Live!', tagline:'', footer:'', alt:'A comedian aims a stage cannon at a watermelon. Front row seats still available. Mother’s Day sold out.'}
    ,{id:'fish-skin-pants', title:'Fish Skin Pants', tagline:'', footer:'Caution: steer clear of cats. Keep refrigerated.', alt:'An admired teen arrives at a 1960s high school dance wearing shimmering patchwork fish-skin pants.'}
    ,{id:'mr-roboto', title:'Mr. Roboto', tagline:'', footer:'Requires 12 D batteries + 8 C batteries. (never included)', alt:'Two excited kids play with a chrome 1980s toy robot beside an inset of its enormous battery compartment.'}
    ,{id:'midtown-underwater-surgery', title:'Midtown Underwater Surgery', tagline:'Too dry, too die', footer:'Outpatient procedures • Extra towels. Schedule your consultation.', alt:'A surgical team calmly operates underwater as a small red plume drifts up and an instrument floats away. A fictional clinic ad with a decorative QR code.'}
    ,{id:'used-books', title:'Used Books', tagline:'10 clean jokes about holes', footer:'Only 49¢', alt:'An orange paperback titled Joke Book faces out on a shelf. A man peeks through a round cutout beneath a large red starburst.'}
    ,{id:'screeching-monkey-hospice', title:'Screeching Monkey Hospice Care', tagline:'You’ll get your life back soon', footer:'', alt:'Three capuchins occupy the chair, bed, and windowsill in a sunlit hospice room. Two are screeching.'}
    ,{id:'bratmans-extra-skinny', title:'Bratman’s Extra Skinny', tagline:'', footer:'', alt:'At a backyard barbecue, guests hold regular-sized buns with extra-long grilled brats hanging straight down from both ends.'}
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
  let viewToken = 0, pendingAd, resumeGame = null;
  function dismiss() {
    if (overlay.hidden) return;
    overlay.hidden = true;
    document.body.classList.remove('scrobbleAdActive');
    const resume = resumeGame;
    resumeGame = null;
    if (resume) {
      document.querySelector('#play')?.focus();
      resume();
    } else {
      window.dispatchEvent(new CustomEvent('scrobble:home'));
      document.querySelector('#newGameDash')?.focus();
    }
  }
  window.ScrobbleFakeAd = {
    get viewToken() { return viewToken; },
    reset() {
      viewToken++;
      resumeGame = null;
      clearTimeout(pendingAd);
      overlay.hidden = true;
      document.body.classList.remove('scrobbleAdActive');
    },
    afterTurn(token, onDismiss = null) {
      clearTimeout(pendingAd);
      pendingAd = setTimeout(() => {
        const show = () => { if (token === viewToken) window.ScrobbleFakeAd.show(onDismiss); };
        if (window.ScrobbleGame?.isMineNoticeOpen?.()) window.ScrobbleGame.waitForMineNotice().then(show);
        else show();
      }, 1600);
    },
    show(onDismiss = null) {
      if (!document.body.classList.contains('scrobbleGameActive') || !overlay.hidden) return;
      resumeGame = onDismiss;
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
    window.ScrobbleFakeAd.reset();
    overlay.hidden = true;
    document.body.classList.remove('scrobbleAdActive');
  });
})();
