/* Ersatz-Vollbild für die App: Das eingebaute Browserfenster bietet Seiten kein echtes Vollbild an
   (Zeitkanal meldet dann „Vollbild wird hier nicht unterstützt“). Da die App schon den ganzen
   Bildschirm füllt, wird das gewünschte Element einfach per CSS über den Bildschirm gelegt.
   Zurück beendet es (window.__rkFsExit). */
(function () {
  if (window.__rkFsExit) return;
  var st = document.createElement('style');
  st.textContent = '.__rkfs{position:fixed!important;left:0!important;top:0!important;right:0!important;bottom:0!important;' +
    'width:100vw!important;height:100vh!important;max-width:none!important;max-height:none!important;margin:0!important;' +
    'border-radius:0!important;transform:none!important;z-index:2147483646!important;background:#000!important}' +
    'video.__rkfs,.__rkfs video{object-fit:contain!important}' +
    '.__rkfs iframe,.__rkfs video{width:100%!important;height:100%!important}';
  (document.head || document.documentElement).appendChild(st);
  var el = null;
  function fire(target) {   // einmal am Element, steigt bis zum Dokument auf
    ['fullscreenchange', 'webkitfullscreenchange'].forEach(function (t) {
      (target || document).dispatchEvent(new Event(t, { bubbles: true }));
    });
    dispatchEvent(new Event('resize'));
  }
  function enter() {
    if (el && el !== this) el.classList.remove('__rkfs');
    el = this;
    if (el !== document.documentElement && el !== document.body) el.classList.add('__rkfs');
    fire(el);
    return Promise.resolve();
  }
  function exit() {
    if (el) { var prev = el; prev.classList.remove('__rkfs'); el = null; fire(prev); }
    return Promise.resolve();
  }
  ['requestFullscreen', 'webkitRequestFullscreen', 'webkitRequestFullScreen', 'mozRequestFullScreen']
    .forEach(function (m) { Element.prototype[m] = enter; });
  ['exitFullscreen', 'webkitExitFullscreen', 'webkitCancelFullScreen', 'mozCancelFullScreen']
    .forEach(function (m) { Document.prototype[m] = exit; });
  ['fullscreenElement', 'webkitFullscreenElement', 'webkitCurrentFullScreenElement', 'mozFullScreenElement']
    .forEach(function (p) { try { Object.defineProperty(document, p, { get: function () { return el; }, configurable: true }); } catch (x) {} });
  ['fullscreenEnabled', 'webkitFullscreenEnabled', 'mozFullScreenEnabled', 'fullscreen', 'webkitIsFullScreen']
    .forEach(function (p) { try { Object.defineProperty(document, p, {
      get: p === 'fullscreen' || p === 'webkitIsFullScreen' ? function () { return !!el; } : function () { return true; },
      configurable: true }); } catch (x) {} });
  window.__rkFsExit = function () { if (!el) return false; exit(); return true; };
})()
