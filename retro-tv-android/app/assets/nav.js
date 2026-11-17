/* Fernbedienungs-Navigation für Seiten, die nicht dafür gebaut sind (Zeitkanal).
   Die App ruft: (dieser Code)('up'|'down'|'left'|'right'|'ok'|'menu'); Zurück ruft window.__rkNavBack().
   Zwei Zustände wie beim Fernseher:
   – Zuschauen: ◀▶ drückt die ⏮/⏭-Knöpfe der Seite (Video), ▲▼ drückt CH+/CH− (Kanal), OK öffnet das Menü.
   – Menü: Steuerkreuz springt zum nächsten anklickbaren Element (türkis umrandet), OK klickt,
     ≡ springt zum Abschnitt „Jahrzehnt“ und zurück nach oben, Zurück schließt das Menü. */
(function () {
  if (window.__rkNav) return window.__rkNav;
  var SEL = 'a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[role=tab],' +
            '[role=option],[role=menuitem],[role=checkbox],[role=switch],[onclick],[tabindex]:not([tabindex="-1"])';
  var style = document.createElement('style');
  style.textContent = '.__rkf{outline:4px solid #4fd1c5!important;outline-offset:3px!important;' +
                      'box-shadow:0 0 0 9px rgba(79,209,197,.35)!important}';
  (document.head || document.documentElement).appendChild(style);
  var cur = null, menuOpen = false, navMode = false, hintTimer = null;
  var tip = document.createElement('div');
  tip.style.cssText = 'position:fixed;left:50%;bottom:6vh;transform:translateX(-50%);z-index:2147483647;' +
    'background:rgba(10,20,35,.92);color:#fff;border:2px solid #4fd1c5;border-radius:999px;padding:10px 22px;' +
    'font:600 20px/1.3 system-ui,sans-serif;pointer-events:none;display:none;white-space:nowrap';
  (document.body || document.documentElement).appendChild(tip);
  function hint(text, ms) {
    tip.textContent = text; tip.style.display = 'block';
    clearTimeout(hintTimer);
    hintTimer = setTimeout(function () { tip.style.display = 'none'; }, ms || 2500);
  }

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
    press(cur);
  }
  function press(e) {
    var r = e.getBoundingClientRect(), o = { bubbles: true, cancelable: true, view: window,
      clientX: r.left + r.width / 2, clientY: r.top + r.height / 2 };
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.tagName) && !/^(checkbox|radio|button|submit)$/.test(e.type)) { e.focus(); return; }
    ['pointerdown', 'mousedown', 'pointerup', 'mouseup'].forEach(function (t) {
      try { e.dispatchEvent(t.indexOf('pointer') === 0 ? new PointerEvent(t, o) : new MouseEvent(t, o)); } catch (x) {}
    });
    e.click();
  }
  function label(e) {
    return ((e.textContent || '') + ' ' + (e.getAttribute('aria-label') || '') + ' ' + (e.getAttribute('title') || '')).trim();
  }
  var KEYS = {   // [genaue Beschriftung, Ersatz-Muster]
    left:  [/^(⏮|⏮️|\|◀|◀◀|«)$/, /vorherig|zurück|previous|\bprev\b/i, 'Vorheriges Video'],
    right: [/^(⏭|⏭️|▶\||▶▶|»)$/, /nächst|weiter|\bnext\b|skip/i, 'Nächstes Video'],
    up:    [/^CH\s*\+$/i, /kanal\s*\+|kanal hoch|channel up/i, 'Kanal +'],
    down:  [/^CH\s*[−–-]$/i, /kanal\s*[−–-]|kanal runter|channel down/i, 'Kanal −']
  };
  function pageButton(dir) {
    var k = KEYS[dir], list = candidates(), i;
    for (i = 0; i < list.length; i++) if (k[0].test((list[i].textContent || '').trim())) return list[i];
    for (i = 0; i < list.length; i++) if (k[1].test(label(list[i]))) return list[i];
    return null;
  }
  function watch(cmd) {   // Zuschauen: Steuerkreuz bedient den Fernseher der Seite
    if (scrollY > 40) toTop();   // irgendwo unten gelandet? Erst zurück zum Bild
    if (cmd === 'ok') { navMode = true; mark(nearTop(candidates()), false); hint('Menü: Pfeile wählen · OK klickt · Zurück schließt', 3500); return; }
    if (cmd === 'menu') { navMode = true; menu(); hint('Einstellungen: Pfeile wählen · OK klickt · Zurück schließt', 3500); return; }
    var b = pageButton(cmd);
    if (b) { press(b); hint(KEYS[cmd][2]); }
    else hint('Kein Knopf für „' + KEYS[cmd][2] + '“ gefunden – OK öffnet das Menü');
  }
  function toTop() {   // zurück zum Bild: Seite und alle verschobenen Bereiche nach oben
    scrollTo(0, 0);
    [].forEach.call(document.querySelectorAll('*'), function (e) { if (e.scrollTop > 0) e.scrollTop = 0; });
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
    if (!navMode) return watch(cmd);
    if (cmd === 'ok') ok(); else if (cmd === 'menu') menu(); else move(cmd);
  };
  window.__rkNavBack = function () {   // Zurück im Menü: Menü schließen, wieder zuschauen
    if (!navMode) return false;
    navMode = false;
    menuOpen = false;
    mark(null);
    toTop();                // immer zurück zum Bild, egal wie weit unten man war
    hint('◀▶ Video · ▲▼ Kanal · OK Menü');
    return true;
  };
  return window.__rkNav;
})()
