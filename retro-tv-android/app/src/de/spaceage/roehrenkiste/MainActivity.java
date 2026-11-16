package de.spaceage.roehrenkiste;

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

/**
 * Röhrenkiste für Fire TV: zeigt die Webseite bildschirmfüllend (ohne Browser, ohne Mauszeiger).
 * Steuerkreuz und OK gehen als normale Tasten an die Seite; ≡, ⏪, ⏩, ⏯ und Zurück
 * reicht die App über window.rkRemote / window.rkBack an die Seite weiter.
 */
public class MainActivity extends Activity {
    static final String URL = "https://zeitkan2.netlify.app/?tv=1&autostart=1";

    WebView web;
    FrameLayout root;
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

        web.setWebViewClient(new WebViewClient());           // Links bleiben in der App
        chrome = new WebChromeClient() {                     // Vollbild von YouTube & Co.
            @Override
            public void onShowCustomView(View view, CustomViewCallback callback) {
                fullscreenView = view;
                fullscreenCallback = callback;
                root.addView(view, new FrameLayout.LayoutParams(-1, -1));
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
        String name = null;
        if (k == KeyEvent.KEYCODE_MENU) name = "menu";
        else if (k == KeyEvent.KEYCODE_MEDIA_FAST_FORWARD) name = "ff";
        else if (k == KeyEvent.KEYCODE_MEDIA_REWIND) name = "rw";
        else if (k == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE || k == KeyEvent.KEYCODE_MEDIA_PLAY
                || k == KeyEvent.KEYCODE_MEDIA_PAUSE) name = "pp";
        if (name != null) {
            if (e.getAction() == KeyEvent.ACTION_DOWN) js("window.rkRemote && rkRemote('" + name + "')", null);
            return true;
        }
        if (k == KeyEvent.KEYCODE_BACK) {
            if (e.getAction() == KeyEvent.ACTION_UP) onRemoteBack();
            return true;
        }
        return super.dispatchKeyEvent(e);
    }

    void onRemoteBack() {
        if (fullscreenView != null) { chrome.onHideCustomView(); return; }
        // erst darf die Seite reagieren (z. B. Menü schließen), sonst zweimal Zurück zum Beenden
        js("window.rkBack ? rkBack() : false", new ValueCallback<String>() {
            @Override
            public void onReceiveValue(String handled) {
                if ("true".equals(handled)) return;
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
