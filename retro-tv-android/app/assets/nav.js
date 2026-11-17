/* Fernbedienungs-Navigation für Seiten, die nicht dafür gebaut sind (Zeitkanal).
   Die App ruft: (dieser Code)('up'|'down'|'left'|'right'|'ok'|'menu').
   Steuerkreuz springt zum nächsten anklickbaren Element in dieser Richtung (türkis umrandet),
   OK klickt es, ≡ springt zum Abschnitt „Jahrzehnt“ und zurück nach oben. */
(function () {
  if (window.__rkNav) return window.__rkNav;
  var SEL = 'a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[role=tab],' +
            '[role=option],[role=menuitem],[role=checkbox],[role=switch],[onclick],[tabindex]:not([tabindex="-1"])';
  var style = document.createElement('style');
  style.textContent = '.__rkf{outline:4px solid #4fd1c5!important;outline-offset:3px!important;' +
                      'box-shadow:0 0 0 9px rgba(79,209,197,.35)!important}';
  (document.head || document.documentElement).appendChild(style);
  var cur = null, menuOpen = false;

  function visible(e) {
    var r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4 || e.disabled) return false;
    var s = getComputedStyle(e);
    return s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0';
  }
  function pointer(e) { return getComputedStyle(e).cursor === 'pointer'; }
  function candidates() {
    var all = [].slice.call(document.querySelectorAll(SEL));
    // klickbare div/span usw. erkennt man am Hand-Mauszeiger; nur das äußerste nehmen
    [].forEach.call(document.querySelectorAll('div,span,li,img,p,td,svg,label'), function (e) {
      if (pointer(e) && !(e.parentElement && pointer(e.parentElement))) all.push(e);
    });
    var out = [];
    all.forEach(function (e) {
      if (out.indexOf(e) >= 0 || !visible(e)) return;
      for (var p = e.parentElement; p; p = p.parentElement) if (p.matches && p.matches(SEL)) return;   // Knopf im Knopf
      out.push(e);
    });
    return out;
  }
  function box(e) {
    var r = e.getBoundingClientRect();
    return { x: r.left + r.width / 2, y: r.top + r.height / 2, l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height };
  }
  function mark(e, scroll) {
    if (cur && cur.classList) cur.classList.remove('__rkf');
    cur = e;
    if (!e) return;
    e.classList.add('__rkf');
    try { e.focus({ preventScroll: true }); } catch (x) {}
    if (scroll) e.scrollIntoView({ block: 'center', inline: 'nearest' });
  }
  function nearTop(list) {   // Startpunkt: sichtbares Element im oberen Bildteil, eher mittig
    var best = null, bd = 1e12;
    list.forEach(function (e) {
      var c = box(e);
      if (c.b < 0 || c.t > innerHeight) return;
      var d = Math.abs(c.y - innerHeight * 0.4) + Math.abs(c.x - innerWidth * 0.5) * 0.5;
      if (d < bd) { bd = d; best = e; }
    });
    return best || list[0];
  }
  function move(dir) {
    var list = candidates(), horiz = dir === 'left' || dir === 'right';
    if (!list.length) { if (!horiz) scrollBy(0, (dir === 'up' ? -1 : 1) * innerHeight * 0.6); return; }
    if (!cur || !document.contains(cur) || !visible(cur)) { mark(nearTop(list), true); return; }
    var a = box(cur), best = null, bs = 1e12;
    list.forEach(function (e) {
      if (e === cur || cur.contains(e) || e.contains(cur)) return;
      var c = box(e);
      var centre = dir === 'left' ? a.x - c.x : dir === 'right' ? c.x - a.x : dir === 'up' ? a.y - c.y : c.y - a.y;
      if (centre <= 1) return;
      var gap = dir === 'left' ? a.l - c.r : dir === 'right' ? c.l - a.r : dir === 'up' ? a.t - c.b : c.t - a.b;
      var overlap = horiz ? Math.min(a.b, c.b) - Math.max(a.t, c.t) : Math.min(a.r, c.r) - Math.max(a.l, c.l);
      var side = horiz ? Math.abs(c.y - a.y) : Math.abs(c.x - a.x);
      var score = Math.max(0, gap) + side * (overlap > 0 ? 0.3 : horiz ? 3 : 1.5);
      if (score < bs) { bs = score; best = e; }
    });
    if (best) mark(best, true);
    else if (!horiz) scrollBy(0, (dir === 'up' ? -1 : 1) * innerHeight * 0.6);
  }
  function ok() {
    if (!cur || !document.contains(cur)) { mark(nearTop(candidates()), true); return; }
    var e = cur, r = e.getBoundingClientRect(), o = { bubbles: true, cancelable: true, view: window,
      clientX: r.left + r.width / 2, clientY: r.top + r.height / 2 };
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.tagName) && !/^(checkbox|radio|button|submit)$/.test(e.type)) { e.focus(); return; }
    ['pointerdown', 'mousedown', 'pointerup', 'mouseup'].forEach(function (t) {
      try { e.dispatchEvent(t.indexOf('pointer') === 0 ? new PointerEvent(t, o) : new MouseEvent(t, o)); } catch (x) {}
    });
    e.click();
  }
  function heading() {
    var hs = document.querySelectorAll('h1,h2,h3,h4,h5,h6,legend,label,p,div,span');
    for (var i = 0; i < hs.length; i++) if (/^jahrzehnte?$/i.test((hs[i].textContent || '').trim())) return hs[i];
    return null;
  }
  function menu() {
    menuOpen = !menuOpen;
    var h = heading();
    if (!menuOpen) {   // zurück nach oben zum Bild
      scrollTo(0, 0);
      if (h) for (var p = h.parentElement; p; p = p.parentElement) if (p.scrollTop > 0) p.scrollTop = 0;
      mark(nearTop(candidates()), false);
      return;
    }
    if (!h) { scrollBy(0, innerHeight * 0.8); return; }
    h.scrollIntoView({ block: 'start' });
    scrollBy(0, -12);
    var hb = h.getBoundingClientRect(), best = null, bd = 1e12;
    candidates().forEach(function (e) {   // erster Knopf unter der Überschrift
      var c = box(e), dy = c.t - hb.top;
      if (dy < -2) return;
      var d = dy * 2 + c.l * 0.2;
      if (d < bd) { bd = d; best = e; }
    });
    mark(best, false);
  }
  window.__rkNav = function (cmd) {
    if (cmd === 'ok') ok(); else if (cmd === 'menu') menu(); else move(cmd);
  };
  return window.__rkNav;
})()
