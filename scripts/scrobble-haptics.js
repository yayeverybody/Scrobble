/* Native feedback is independent of action handlers and must never block them. */
(() => {
  'use strict';
  if (window.ScrobbleHaptics) return;
  let plugin;
  function nativeHaptics() {
    const cap = window.Capacitor;
    if (!cap?.isNativePlatform?.()) return null;
    if (!plugin) plugin = cap.Plugins?.Haptics || cap.registerPlugin?.('Haptics');
    return plugin;
  }
  function send(method, options) {
    try {
      const native = nativeHaptics();
      if (native?.[method]) Promise.resolve(native[method](options)).catch(() => {});
    } catch (_) { /* An unavailable plugin must not interrupt gameplay. */ }
  }
  const feedback = {
    tap: () => send('impact', { style: 'LIGHT' }),
    create: () => send('impact', { style: 'MEDIUM' }),
    success: () => send('notification', { type: 'SUCCESS' })
  };
  window.ScrobbleHaptics = feedback;
  document.addEventListener('click', event => {
    if (!event.isTrusted) return;
    const button = event.target?.closest?.('button');
    if (!button || button.disabled || button.getAttribute('aria-disabled') === 'true') return;
    if (button.id === 'startFriendGame' || button.hasAttribute('data-cpu-difficulty')) feedback.create();
    else feedback.tap();
  }, true);
  document.addEventListener('change', event => {
    if (event.isTrusted && event.target?.matches?.('#gameModeBox .weirdChoice input') && !event.target.disabled) feedback.tap();
  }, true);
  window.addEventListener('scrobble:turn-ended', event => {
    if (event.detail?.move_type === 'play') feedback.success();
    else if (['pass', 'swap'].includes(event.detail?.move_type)) feedback.create();
  });
})();
