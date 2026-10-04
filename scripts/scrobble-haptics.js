/* Feedback follows accepted actions and score animation; it never blocks gameplay. */
(() => {
  'use strict';
  if (window.ScrobbleHaptics) return;
  const scorePulses = new Map();
  let basic, custom;
  const settings = { sound: true, haptics: true };
  for (const key of Object.keys(settings)) {
    try { settings[key] = localStorage.getItem('scrobble-feedback-' + key) !== 'off'; } catch (_) {}
    const input = document.getElementById('feedback-' + key);
    if (input) {
      input.checked = settings[key];
      input.addEventListener('change', () => {
        settings[key] = input.checked;
        try { localStorage.setItem('scrobble-feedback-' + key, input.checked ? 'on' : 'off'); } catch (_) {}
        if (!input.checked) cancelAll();
      });
    }
  }
  function plugins() {
    const cap = window.Capacitor;
    if (!cap?.isNativePlatform?.()) return false;
    if (!basic) basic = cap.Plugins?.Haptics || cap.registerPlugin?.('Haptics');
    if (!custom && cap.isPluginAvailable?.('ScrobbleFeedback')) custom = cap.Plugins?.ScrobbleFeedback || cap.registerPlugin?.('ScrobbleFeedback');
    return true;
  }
  function fallback(kind, progress) {
    if (!settings.haptics) return;
    try {
      const method = kind === 'finish' ? 'notification' : 'impact';
      const options = kind === 'finish' ? { type: 'SUCCESS' } : { style: kind === 'tap' || kind === 'return' || progress < .33 ? 'LIGHT' : progress > .66 ? 'HEAVY' : 'MEDIUM' };
      Promise.resolve(basic?.[method]?.(options)).catch(() => {});
    } catch (_) {}
  }
  function play(kind, options = {}) {
    if (document.hidden || !plugins()) return;
    const payload = { kind, ...options, haptics: settings.haptics, sound: settings.sound && ['score', 'finish'].includes(kind) };
    try {
      if (custom) Promise.resolve(custom.play(payload)).then(result => { if (result?.audioError) console.warn('Scrobble scoring audio:', result.audioError); }).catch(() => fallback(kind, options.progress));
      else fallback(kind, options.progress);
    } catch (_) { fallback(kind, options.progress); }
  }
  const testSound = document.getElementById('feedback-test');
  if (testSound) testSound.addEventListener('click', async () => {
    const status = document.getElementById('feedback-test-status');
    if (!status) return;
    if (!settings.sound) { status.textContent = 'Enable Scoring sounds first.'; return; }
    if (!plugins() || !custom) { status.textContent = 'Sound test requires the updated iPhone app.'; return; }
    testSound.disabled = true;
    status.textContent = 'Testing sound…';
    try {
      const result = await custom.play({ kind: 'finish', key: 'test', gain: 30, sound: true, haptics: false });
      status.textContent = result?.audioPlayed ? 'Test chime played. Silent Mode must be off to hear it.' : 'Sound could not play: ' + (result?.audioError || 'Audio player unavailable.');
    } catch (_) { status.textContent = 'Sound test unavailable. Please reopen the app.'; }
    finally { testSound.disabled = false; }
  });
  function cancel(slot) {
    if (!scorePulses.delete(slot)) return;
    try { if (custom) Promise.resolve(custom.cancel({ key: 'score-' + slot })).catch(() => {}); } catch (_) {}
  }
  function cancelAll() {
    for (const slot of [...scorePulses.keys()]) cancel(slot);
    try { if (custom) Promise.resolve(custom.cancel({ key: '*' })).catch(() => {}); } catch (_) {}
  }
  const feedback = {
    tap: () => play('tap'),
    create: () => play('create'),
    success: () => play('finish'),
    tile: () => play('tile'),
    tileReturn: () => play('return'),
    error: () => play('error'),
    scoreCancel: cancel,
    scoreStart(slot, gain) {
      cancel(slot);
      if (gain > 0 && !document.hidden) scorePulses.set(slot, { last: -Infinity, gain });
    },
    scoreProgress(slot, progress, now) {
      const pulse = scorePulses.get(slot);
      if (!pulse || progress >= 1 || now - pulse.last < (260 - 165 * progress) / 1.3) return;
      pulse.last = now;
      play('score', { key: 'score-' + slot, progress, gain: pulse.gain });
    },
    scoreEnd(slot) {
      const pulse = scorePulses.get(slot);
      if (!pulse) return;
      scorePulses.delete(slot);
      play('finish', { key: 'score-' + slot, gain: pulse.gain });
    }
  };
  window.ScrobbleHaptics = feedback;
  document.addEventListener('visibilitychange', () => { if (document.hidden) cancelAll(); });
  window.addEventListener('scrobble:home', cancelAll);
  document.addEventListener('click', event => {
    if (!event.isTrusted) return;
    const button = event.target?.closest?.('button');
    if (!button || button.disabled || button.getAttribute('aria-disabled') === 'true') return;
    // Successful tile placement provides its own precise feedback.
    if (button.closest?.('.cell') || button.closest?.('.rackbtn')) return;
    if (button.id === 'startFriendGame' || button.hasAttribute('data-cpu-difficulty')) feedback.create();
    else feedback.tap();
  }, true);
  document.addEventListener('change', event => {
    if (event.isTrusted && event.target?.matches?.('#gameModeBox .weirdChoice input') && !event.target.disabled) feedback.tap();
  }, true);
  window.addEventListener('scrobble:turn-ended', event => {
    if (['pass', 'swap'].includes(event.detail?.move_type)) feedback.create();
  });
})();
