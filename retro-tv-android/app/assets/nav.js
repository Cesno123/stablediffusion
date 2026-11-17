/* Fernbedienungs-Navigation für Seiten, die nicht dafür gebaut sind (Zeitkanal).
   Die App ruft: (dieser Code)('up'|'down'|'left'|'right'|'ok'|'menu'); Zurück ruft window.__rkNavBack().
   Belegung (Wunsch des Nutzers):
   – ≡ (menu): Einstellungen („Jahrzehnt“ …) anwählen – egal, wo man gerade ist.
   – OK beim Zuschauen: Knopfreihe unter dem Fernseher (⏮ ⏭ CH− AN …) anwählen.
   – ⏯ (list): Playlist anwählen (laufender Eintrag, sonst erster).
   – ⏪ / ⏩ (prev/next): vorheriges / nächstes Video, immer – auch im Vollbild und im Menü.
   – ◀▶ beim Zuschauen: ⏮/⏭ der Seite (Video); ▲▼ beim Zuschauen: CH+/CH−.
   – Angewählt (türkis umrandet): Pfeile wählen, OK drückt; Zurück = zurück zum Bild. */
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
  /* Lange Listen (z. B. Programmliste mit ~2000 Einträgen): Behälter, in dem mindestens 12 anklickbare
     Elemente untereinander stehen. Mit ▲ wird so eine Liste übersprungen (sonst landet man auf dem
     letzten Eintrag), mit ▼ betritt man sie oben; drinnen verlässt ◀ / ▶ sie nach oben / unten. */
  function bigList(e, list) {
    for (var p = e.parentElement; p && p !== document.body && p !== document.documentElement; p = p.parentElement) {
      if (p.children.length < 12) continue;
      var rows = {}, n = 0;   // nur echte Listen: Einträge untereinander (≥ 10 Zeilen), nicht eine Knopfreihe
      for (var i = 0; i < list.length && n < 10; i++) {
        if (!p.contains(list[i])) continue;
        var t = Math.round(list[i].getBoundingClientRect().top / 4);
        if (!rows[t]) { rows[t] = 1; n++; }
      }
      if (n >= 10) return p;
    }
    return null;
  }
  function pick(dir, list, skip) {   // nächstes Element in Richtung dir, ohne die in skip
    var horiz = dir === 'left' || dir === 'right', a = box(cur), best = null, bs = 1e12;
    list.forEach(function (e) {
      if (e === cur || cur.contains(e) || e.contains(cur) || (skip && skip.contains(e))) return;
      var c = box(e);
      var centre = dir === 'left' ? a.x - c.x : dir === 'right' ? c.x - a.x : dir === 'up' ? a.y - c.y : c.y - a.y;
      if (centre <= 1) return;
      var gap = dir === 'left' ? a.l - c.r : dir === 'right' ? c.l - a.r : dir === 'up' ? a.t - c.b : c.t - a.b;
      var overlap = horiz ? Math.min(a.b, c.b) - Math.max(a.t, c.t) : Math.min(a.r, c.r) - Math.max(a.l, c.l);
      var side = horiz ? Math.abs(c.y - a.y) : Math.abs(c.x - a.x);
      var score = Math.max(0, gap) + side * (overlap > 0 ? 0.3 : horiz ? 3 : 1.5);
      if (score < bs) { bs = score; best = e; }
    });
    return best;
  }
  function move(dir) {
    var list = candidates(), horiz = dir === 'left' || dir === 'right';
    if (!list.length) { if (!horiz) scrollBy(0, (dir === 'up' ? -1 : 1) * innerHeight * 0.6); return; }
    if (!cur || !document.contains(cur) || !visible(cur)) { mark(nearTop(list), true); return; }
    var inList = bigList(cur, list), best;
    if (inList && horiz) {   // in der Liste: ◀ / ▶ verlassen sie nach oben / unten
      best = pick(dir === 'left' ? 'up' : 'down', list, inList);
      if (best) { mark(best, true); hint('Liste verlassen'); }
      return;
    }
    best = pick(dir, list, null);
    if (best && dir === 'up') {
      var target = bigList(best, list);
      if (target && target !== inList && !target.contains(cur)) best = pick('up', list, target) || best;   // Liste überspringen
    }
    if (best) {
      mark(best, true);
      var entered = bigList(best, list);
      if (entered && entered !== inList) hint('Liste: ▲▼ wählen · OK abspielen · ◀ ▶ Liste verlassen', 4000);
    }
    else if (!horiz) scrollBy(0, (dir === 'up' ? -1 : 1) * innerHeight * 0.6);
  }
  function ok() {
    if (!cur || !document.contains(cur)) { mark(nearTop(candidates()), true); return; }
    press(cur);
  }
  function press(e) {
    if (!visible(e)) { e.click(); return; }   // ausgeblendeter Knopf: nur klicken
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
    var k = KEYS[dir], lists = [candidates(), [].slice.call(document.querySelectorAll(SEL + ',div,span'))], i, j;
    // erst sichtbare Knöpfe; dann auch ausgeblendete (Zeitkanal versteckt sie im Vollbild – click() wirkt trotzdem)
    for (j = 0; j < lists.length; j++) {
      var list = lists[j];
      for (i = 0; i < list.length; i++) if (k[0].test((list[i].textContent || '').trim())) return list[i];
      for (i = 0; i < list.length; i++) if (j === 0 && k[1].test(label(list[i]))) return list[i];
    }
    for (i = 0; i < lists[1].length; i++) {   // ausgeblendet: Ersatz-Muster nur bei echten Knöpfen
      var e = lists[1][i];
      if (e.matches(SEL) && k[1].test(label(e))) return e;
    }
    return null;
  }
  function sendKey(dir) {   // kein Knopf gefunden: Pfeiltaste direkt an die Seite
    var names = { left: ['ArrowLeft', 37], right: ['ArrowRight', 39], up: ['ArrowUp', 38], down: ['ArrowDown', 40] }[dir];
    var target = document.activeElement && document.activeElement !== document.body ? document.activeElement : document;
    ['keydown', 'keyup'].forEach(function (t) {
      target.dispatchEvent(new KeyboardEvent(t, { key: names[0], code: names[0], keyCode: names[1], which: names[1], bubbles: true }));
    });
  }
  function watch(cmd) {   // Zuschauen: Steuerkreuz bedient den Fernseher der Seite
    if (scrollY > 40 && !document.fullscreenElement) toTop();   // irgendwo unten gelandet? Erst zurück zum Bild
    if (cmd === 'ok' || cmd === 'menu' || cmd === 'list') return go(cmd);
    var b = pageButton(cmd);
    if (b) { press(b); hint(KEYS[cmd][2]); }
    else { sendKey(cmd); hint(KEYS[cmd][2] + ' (Taste an die Seite geschickt)'); }
  }
  /* Anspringen: Knopfreihe (ok), Einstellungen (menu), Playlist (list) – danach Pfeile/OK im angewählten Bereich */
  function go(cmd) {
    navMode = true;
    if (cmd === 'menu') { menuOpen = false; menu(); hint('Menü: Pfeile wählen · OK drückt · Zurück = Bild', 3500); return; }
    if (cmd === 'list') {
      var list = candidates(), counts = [], best = null, max = 0;
      list.forEach(function (e) {   // größte Liste der Seite
        var l = bigList(e, list);
        if (!l) return;
        var i = counts.findIndex(function (c) { return c.l === l; });
        if (i < 0) counts.push({ l: l, n: 1 }); else counts[i].n++;
      });
      counts.forEach(function (c) { if (c.n > max) { max = c.n; best = c.l; } });
      if (!best) { hint('Keine Playlist gefunden'); return; }
      var items = list.filter(function (e) { return best.contains(e); });
      var now = items.filter(function (e) {   // laufenden Eintrag bevorzugen
        return e.getAttribute('aria-current') || e.getAttribute('aria-selected') === 'true' ||
               /(^|[\s_-])(active|current|playing|now|selected|on)([\s_-]|$)/i.test(e.className + ' ' + (e.parentElement ? e.parentElement.className : ''));
      })[0];
      mark(now || items[0], true);
      hint('Playlist: ▲▼ wählen · OK spielt · Zurück = Bild', 3500);
      return;
    }
    // ok: Knopfreihe unter dem Fernseher – über den ⏮-Knopf gefunden, sonst ein Knopf oben im Bild
    var first = pageButton('left') || pageButton('right') || pageButton('down') || pageButton('up');
    toTop();
    mark(first || nearTop(candidates()), false);
    hint('Knöpfe: Pfeile wählen · OK drückt · Zurück = Bild', 3500);
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
  function skip(dir) {   // ⏪ / ⏩: Video zurück / vor – in jedem Zustand, auch im Vollbild
    var b = pageButton(dir), txt = KEYS[dir][2];
    if (b) { press(b); hint(txt + ' (' + ((b.textContent || '').trim() || label(b)).slice(0, 12) + ')'); }
    else { sendKey(dir); hint(txt + ' – kein Knopf gefunden, Taste an die Seite geschickt', 3500); }
  }
  window.__rkNav = function (cmd) {
    if (cmd === 'prev') return skip('left');
    if (cmd === 'next') return skip('right');
    if (!navMode) return watch(cmd);
    if (cmd === 'menu' || cmd === 'list') go(cmd); else if (cmd === 'ok') ok(); else move(cmd);
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
