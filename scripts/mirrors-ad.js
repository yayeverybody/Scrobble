/* A fictional sponsor. Bundled artwork; no network, tracking, purchases or timers. */
(() => {
  'use strict';
  const overlay = document.getElementById('mirrorsAd');
  const close = document.getElementById('mirrorsAdClose');
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
