package de.spaceage.tvapp;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;
import android.widget.TextView;
import android.view.Gravity;
import android.os.SystemClock;
import android.view.MotionEvent;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;

/**
 * Fire-TV-Hülle für eine Webseite (Röhrenkiste, Zeitkanal …): bildschirmfüllend, ohne Browser,
 * ohne Mauszeiger. Steuerkreuz und OK gehen als normale Tasten an die Seite.
 * ≡, ⏪, ⏩, ⏯ und Zurück: Hat die Seite window.rkRemote / window.rkBack (Röhrenkiste), bekommt sie
 * die Tasten; sonst steuert die App das erste Video der Seite selbst und blättert mit Zurück zurück.
 * Die Adresse kommt aus Config.URL (von build.sh aus flavors/*.conf erzeugt).
 */
public class MainActivity extends Activity {
    static final String URL = Config.URL;
    /** ≡ bei Seiten mit Zeiger (Zeitkanal): zum Abschnitt „Jahrzehnt“ springen bzw. zurück nach oben.
     *  Liefert die Mitte des ersten Knopfes dort (CSS-Pixel), damit der Zeiger gleich darauf steht. */
    static final String MENU_JS =
        "(function(open){var hs=[].slice.call(document.querySelectorAll('h1,h2,h3,h4,h5,h6,legend,label,p,div,span')),h=null;" +
        "for(var i=0;i<hs.length;i++){if(/^jahrzehnte?$/i.test((hs[i].textContent||'').trim())){h=hs[i];break;}}" +
        "if(!open){window.scrollTo(0,0);if(h){for(var p=h.parentElement;p;p=p.parentElement){if(p.scrollTop>0)p.scrollTop=0;}}return '';}" +
        "if(!h){window.scrollBy(0,window.innerHeight*0.8);return '';}" +
        "h.scrollIntoView({block:'start'});window.scrollBy(0,-12);" +
        "var b=null,n=h;while(n&&!b){var s=n.nextElementSibling;while(s&&!b){b=s.matches('button,a,[role=button],input,select')?s:" +
        "s.querySelector('button,a,[role=button],input,select');s=s.nextElementSibling;}n=n.parentElement;}" +
        "var r=(b||h).getBoundingClientRect();return Math.round(r.left+r.width/2)+','+Math.round(r.top+r.height/2);})";
    /** Für Seiten ohne Röhrenkiste-Schnittstelle: Video direkt steuern, sonst Taste als Tastendruck schicken. */
    static final String REMOTE_JS =
        "(function(n){if(window.rkRemote){rkRemote(n);return;}" +
        "var v=document.querySelector('video');" +
        "if(v&&n!=='menu'){if(n==='ff')v.currentTime=Math.min(v.duration||1e9,v.currentTime+30);" +
        "else if(n==='rw')v.currentTime=Math.max(0,v.currentTime-30);else{v.paused?v.play():v.pause();}return;}" +
        "var k={ff:['MediaFastForward',228],rw:['MediaRewind',227],pp:['MediaPlayPause',179],menu:['ContextMenu',93]}[n];" +
        "(document.activeElement||document).dispatchEvent(new KeyboardEvent('keydown',{key:k[0],keyCode:k[1],bubbles:true}));})";

    WebView web;
    FrameLayout root;
    CursorView cursor;          // nur bei Config.CURSOR (Seiten ohne Fernbedienungs-Steuerung)
    long touchDown;
    TextView diag;              // Anzeige oben rechts: empfangene Taste und Ergebnis (nur Config.NAV)
    final Runnable hideDiag = new Runnable() { public void run() { diag.setVisibility(View.GONE); } };
    boolean pageMenuOpen;
    String navJs;               // assets/nav.js – nur bei Config.NAV
    String fsJs;                // assets/fullscreen.js – Ersatz-Vollbild, nur bei Config.NAV
    final Runnable hideCursor = new Runnable() { public void run() { cursor.setVisibility(View.INVISIBLE); } };
    View fullscreenView;
    WebChromeClient.CustomViewCallback fullscreenCallback;
    WebChromeClient chrome;
    long lastBack;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON | WindowManager.LayoutParams.FLAG_FULLSCREEN);
        root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);      // Sendungen starten ohne zusätzlichen Klick
        s.setUserAgentString(s.getUserAgentString() + " RoehrenkisteTV");
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, true);   // Netlify-Anmeldung, YouTube

        web.setWebViewClient(new WebViewClient() {           // Links bleiben in der App
            @Override
            public void onPageFinished(WebView view, String url) {
                if (fsJs != null) js(fsJs, null);             // Ersatz-Vollbild bereitstellen
            }
        });
        chrome = new WebChromeClient() {                     // Vollbild von YouTube & Co.
            @Override
            public void onShowCustomView(View view, CustomViewCallback callback) {
                fullscreenView = view;
                fullscreenCallback = callback;
                root.addView(view, new FrameLayout.LayoutParams(-1, -1));
                if (diag != null) diag.bringToFront();   // Anzeige auch über dem Vollbild
                web.setVisibility(View.GONE);
            }

            @Override
            public void onHideCustomView() {
                if (fullscreenView == null) return;
                root.removeView(fullscreenView);
                fullscreenView = null;
                web.setVisibility(View.VISIBLE);
                if (fullscreenCallback != null) fullscreenCallback.onCustomViewHidden();
                web.requestFocus();
            }
        };
        web.setWebChromeClient(chrome);

        root.addView(web, new FrameLayout.LayoutParams(-1, -1));
        if (Config.NAV) {
            navJs = readAsset("nav.js").trim().replaceAll(";$", "");
            fsJs = readAsset("fullscreen.js").trim().replaceAll(";$", "") + ";";
        }
        if (Config.CURSOR) {
            cursor = new CursorView(this);
            root.addView(cursor, new FrameLayout.LayoutParams(-1, -1));
            root.post(new Runnable() { public void run() {
                cursor.x = root.getWidth() / 2f; cursor.y = root.getHeight() / 2f; showCursor(); } });
        }
        if (Config.NAV) {
            diag = new TextView(this);
            diag.setTextColor(Color.WHITE);
            diag.setTextSize(16);
            diag.setBackgroundColor(0xCC0F2440);
            float d = getResources().getDisplayMetrics().density;
            diag.setPadding(Math.round(12 * d), Math.round(6 * d), Math.round(12 * d), Math.round(6 * d));
            FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.END);
            lp.setMargins(0, Math.round(12 * d), Math.round(12 * d), 0);
            root.addView(diag, lp);
            String ver = "?";
            try { ver = getPackageManager().getPackageInfo(getPackageName(), 0).versionName; } catch (Exception ignored) { }
            showDiag("Zeitkanal-App " + ver + " · ⏪⏩ Video · ≡ Menü · OK Knöpfe · ⏯ Playlist", 6000);
        }
        setContentView(root);
        if (state != null) web.restoreState(state); else web.loadUrl(URL);
        web.requestFocus();
    }

    void js(String code, ValueCallback<String> callback) {
        web.evaluateJavascript(code, callback);
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent e) {
        int k = e.getKeyCode();
        if (diag != null && e.getAction() == KeyEvent.ACTION_DOWN && e.getRepeatCount() == 0)
            showDiag("Taste: " + KeyEvent.keyCodeToString(k).replace("KEYCODE_", "")
                    + (fullscreenView != null ? " · Vollbild" : ""), 4000);
        if (navJs != null && navKey(e)) return true;   // auch im Vollbild: Zeitkanal löst eigenes Vollbild aus
        if (cursor != null && fullscreenView == null && cursorKey(e)) return true;
        if (cursor != null && k == KeyEvent.KEYCODE_MENU) {
            if (e.getAction() == KeyEvent.ACTION_DOWN && e.getRepeatCount() == 0) togglePageMenu();
            return true;
        }
        String name = null;
        if (k == KeyEvent.KEYCODE_MENU) name = "menu";
        else if (k == KeyEvent.KEYCODE_MEDIA_FAST_FORWARD) name = "ff";
        else if (k == KeyEvent.KEYCODE_MEDIA_REWIND) name = "rw";
        else if (k == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE || k == KeyEvent.KEYCODE_MEDIA_PLAY
                || k == KeyEvent.KEYCODE_MEDIA_PAUSE) name = "pp";
        if (name != null) {
            if (e.getAction() == KeyEvent.ACTION_DOWN) js(REMOTE_JS + "('" + name + "')", null);
            return true;
        }
        if (k == KeyEvent.KEYCODE_BACK) {
            if (e.getAction() == KeyEvent.ACTION_UP) onRemoteBack();
            return true;
        }
        return super.dispatchKeyEvent(e);
    }

    /** Fernbedienungs-Navigation (assets/nav.js): Steuerkreuz springt von Knopf zu Knopf, OK klickt, ≡ = Einstellungen. */
    boolean navKey(KeyEvent e) {
        int k = e.getKeyCode();
        String cmd = k == KeyEvent.KEYCODE_DPAD_UP ? "up" : k == KeyEvent.KEYCODE_DPAD_DOWN ? "down"
                : k == KeyEvent.KEYCODE_DPAD_LEFT ? "left" : k == KeyEvent.KEYCODE_DPAD_RIGHT ? "right"
                : (k == KeyEvent.KEYCODE_DPAD_CENTER || k == KeyEvent.KEYCODE_ENTER || k == KeyEvent.KEYCODE_NUMPAD_ENTER) ? "ok"
                : k == KeyEvent.KEYCODE_MENU ? "menu"
                : (k == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE || k == KeyEvent.KEYCODE_MEDIA_PLAY
                   || k == KeyEvent.KEYCODE_MEDIA_PAUSE) ? "list"                  // ⏯ = Playlist
                : k == KeyEvent.KEYCODE_MEDIA_REWIND ? "prev"                    // ⏪ = vorheriges Video
                : k == KeyEvent.KEYCODE_MEDIA_FAST_FORWARD ? "next" : null;      // ⏩ = nächstes Video
        if (cmd == null) return false;
        boolean repeatable = cmd.equals("up") || cmd.equals("down") || cmd.equals("left") || cmd.equals("right");
        if (e.getAction() == KeyEvent.ACTION_DOWN && (repeatable || e.getRepeatCount() == 0)) {
            // Klammer um navJs: sonst würde der mehrzeilige Kommentar am Anfang die Anweisung beenden
            final String c = cmd;
            // echtes Vollbild (z. B. aus dem Videoplayer): für Menü, Knöpfe und Playlist erst beenden
            if (fullscreenView != null && (cmd.equals("menu") || cmd.equals("ok") || cmd.equals("list"))) chrome.onHideCustomView();
            String code = "(function(){try{window.__rkLastHint='';" + fsJs + "var r=(" + navJs + ")('" + cmd + "');"
                    + "return window.__rkLastHint||'ok';}catch(x){return 'Fehler: '+(x&&x.message)}})()";
            js(code, new ValueCallback<String>() {
                @Override
                public void onReceiveValue(String v) {   // Ergebnis neben der Taste anzeigen
                    v = v == null ? "keine Antwort" : v.replace("\"", "");
                    if (diag != null && !c.equals("up") && !c.equals("down") && !c.equals("left") && !c.equals("right") || v.startsWith("Fehler"))
                        showDiag(diag.getText() + " → " + v, 5000);
                }
            });
        }
        return true;
    }

    String readAsset(String name) {
        try (InputStream in = getAssets().open(name)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            for (int n; (n = in.read(buf)) > 0; ) out.write(buf, 0, n);
            return out.toString("UTF-8");
        } catch (Exception ex) {
            return null;
        }
    }

    /** ≡ bei Seiten ohne eigenes Menü: Einstellungen anspringen und Zeiger daraufsetzen; nochmal ≡ = zurück zum Bild. */
    void togglePageMenu() {
        pageMenuOpen = !pageMenuOpen;
        js(MENU_JS + "(" + pageMenuOpen + ")", new ValueCallback<String>() {
            @Override
            public void onReceiveValue(String v) {
                v = v == null ? "" : v.replace("\"", "");
                float d = getResources().getDisplayMetrics().density;
                String[] xy = v.split(",");
                if (xy.length == 2) {
                    try { cursor.x = Float.parseFloat(xy[0]) * d; cursor.y = Float.parseFloat(xy[1]) * d; }
                    catch (NumberFormatException ignored) { }
                } else {
                    cursor.x = root.getWidth() / 2f; cursor.y = root.getHeight() / 2f;
                }
                cursor.x = Math.max(cursor.r, Math.min(root.getWidth() - cursor.r, cursor.x));
                cursor.y = Math.max(cursor.r, Math.min(root.getHeight() - cursor.r, cursor.y));
                showCursor();
            }
        });
    }

    void showDiag(String text, int ms) {
        if (diag == null) return;
        diag.setText(text);
        diag.setVisibility(View.VISIBLE);
        diag.bringToFront();
        diag.removeCallbacks(hideDiag);
        diag.postDelayed(hideDiag, ms);
    }

    void showCursor() {
        cursor.setVisibility(View.VISIBLE);
        cursor.invalidate();
        cursor.removeCallbacks(hideCursor);
        cursor.postDelayed(hideCursor, 5000);   // beim Zuschauen nicht im Bild stehen lassen
    }

    /** Steuerkreuz bewegt den Zeiger (schneller beim Gedrückthalten), am Rand wird geblättert; OK tippt. */
    boolean cursorKey(KeyEvent e) {
        int k = e.getKeyCode();
        boolean down = e.getAction() == KeyEvent.ACTION_DOWN;
        if (k == KeyEvent.KEYCODE_DPAD_CENTER || k == KeyEvent.KEYCODE_ENTER || k == KeyEvent.KEYCODE_NUMPAD_ENTER) {
            if (cursor.getVisibility() != View.VISIBLE) { if (!down) showCursor(); return true; }   // erst zeigen, dann klicken
            long now = SystemClock.uptimeMillis();
            if (down && e.getRepeatCount() == 0) touchDown = now;
            if (down && e.getRepeatCount() > 0) return true;
            MotionEvent m = MotionEvent.obtain(touchDown, now, down ? MotionEvent.ACTION_DOWN : MotionEvent.ACTION_UP, cursor.x, cursor.y, 0);
            m.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);
            web.dispatchTouchEvent(m);
            m.recycle();
            showCursor();
            return true;
        }
        int dx = k == KeyEvent.KEYCODE_DPAD_LEFT ? -1 : k == KeyEvent.KEYCODE_DPAD_RIGHT ? 1 : 0;
        int dy = k == KeyEvent.KEYCODE_DPAD_UP ? -1 : k == KeyEvent.KEYCODE_DPAD_DOWN ? 1 : 0;
        if (dx == 0 && dy == 0) return false;
        if (!down) return true;
        float density = getResources().getDisplayMetrics().density;
        float step = density * (14 + Math.min(e.getRepeatCount(), 15) * 4);
        float nx = cursor.x + dx * step, ny = cursor.y + dy * step;
        float w = root.getWidth(), h = root.getHeight(), edge = cursor.r;
        if (ny < edge) { web.scrollBy(0, Math.round(ny - edge)); ny = edge; }
        if (ny > h - edge) { web.scrollBy(0, Math.round(ny - (h - edge))); ny = h - edge; }
        cursor.x = Math.max(edge, Math.min(w - edge, nx));
        cursor.y = ny;
        showCursor();
        return true;
    }

    void onRemoteBack() {
        if (fullscreenView != null) { chrome.onHideCustomView(); return; }
        // erst darf die Seite reagieren (z. B. Menü schließen), sonst zweimal Zurück zum Beenden
        js("window.rkBack ? rkBack() : ((window.__rkNavBack && __rkNavBack()) || (window.__rkFsExit ? __rkFsExit() : false))", new ValueCallback<String>() {
            @Override
            public void onReceiveValue(String handled) {
                if ("true".equals(handled)) return;
                if (web.canGoBack()) { web.goBack(); return; }
                long now = System.currentTimeMillis();
                if (now - lastBack < 2500) { finish(); return; }
                lastBack = now;
                Toast.makeText(MainActivity.this, "Nochmal Zurück drücken zum Beenden", Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override protected void onSaveInstanceState(Bundle out) { super.onSaveInstanceState(out); web.saveState(out); }
    @Override protected void onPause() { super.onPause(); web.onPause(); CookieManager.getInstance().flush(); }
    @Override protected void onResume() { super.onResume(); web.onResume(); }
    @Override protected void onDestroy() { web.destroy(); super.onDestroy(); }
}
