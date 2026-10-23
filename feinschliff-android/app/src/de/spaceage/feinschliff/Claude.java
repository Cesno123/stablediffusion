package de.spaceage.feinschliff;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

import org.json.JSONArray;
import org.json.JSONObject;

/** One request to the Claude Messages API (raw HTTPS: no Android SDK toolchain is available to bundle the Java SDK). */
final class Claude {
    static final String MODEL = "claude-opus-5-5";

    private Claude() {}

    /** Sends the prompt (and an optional JPEG as base64) and returns Claude's text, or throws with a German message. */
    static String ask(String apiKey, String prompt, String jpegBase64) throws Exception {
        try {
            return ask(apiKey, prompt, jpegBase64, true);
        } catch (FallbackRejected e) {  // account without the refusal-fallback beta: ask once more without it
            return ask(apiKey, prompt, jpegBase64, false);
        }
    }

    private static final class FallbackRejected extends Exception {}

    private static String ask(String apiKey, String prompt, String jpegBase64, boolean withFallback) throws Exception {
        JSONArray content = new JSONArray();
        if (jpegBase64 != null) {
            content.put(new JSONObject().put("type", "image").put("source", new JSONObject()
                    .put("type", "base64").put("media_type", "image/jpeg").put("data", jpegBase64)));
        }
        content.put(new JSONObject().put("type", "text").put("text", prompt));
        JSONObject body = new JSONObject()
                .put("model", MODEL)
                .put("max_tokens", 8000)
                .put("output_config", new JSONObject().put("effort", "low"))
                .put("messages", new JSONArray().put(new JSONObject().put("role", "user").put("content", content)));

        if (withFallback) body.put("fallbacks", "default");  // on a refusal the API retries on a suitable fallback model
        HttpURLConnection c = (HttpURLConnection) new URL("https://api.anthropic.com/v1/messages").openConnection();
        c.setRequestMethod("POST");
        c.setConnectTimeout(15000);
        c.setReadTimeout(180000);
        c.setDoOutput(true);
        c.setRequestProperty("content-type", "application/json");
        c.setRequestProperty("x-api-key", apiKey.trim());
        c.setRequestProperty("anthropic-version", "2023-06-01");
        if (withFallback) c.setRequestProperty("anthropic-beta", "server-side-fallback-2026-07-01");
        OutputStream os = c.getOutputStream();
        os.write(body.toString().getBytes("UTF-8"));
        os.close();

        int code = c.getResponseCode();
        String raw = read(code >= 400 ? c.getErrorStream() : c.getInputStream());
        if (code >= 400) {
            String msg = "";
            try { msg = new JSONObject(raw).getJSONObject("error").optString("message"); } catch (Exception ignored) {}
            if (withFallback && code == 400 && (msg.contains("fallback") || msg.contains("beta"))) throw new FallbackRejected();
            if (code == 401) throw new Exception("Der API-Schlüssel ist ungültig. Prüfe ihn in den Einstellungen.");
            if (code == 402 || msg.toLowerCase().contains("credit")) throw new Exception("Kein Guthaben mehr. Lade es auf console.anthropic.com auf.");
            if (code == 429) throw new Exception("Zu viele Anfragen. Bitte kurz warten.");
            if (code >= 500) throw new Exception("Claude ist gerade überlastet. Bitte noch einmal versuchen.");
            throw new Exception("Fehler " + code + ": " + msg);
        }
        JSONObject res = new JSONObject(raw);
        if ("refusal".equals(res.optString("stop_reason"))) throw new Exception("Diese Anfrage wurde abgelehnt. Formuliere sie anders.");
        StringBuilder out = new StringBuilder();
        JSONArray blocks = res.getJSONArray("content");
        for (int i = 0; i < blocks.length(); i++) {
            JSONObject b = blocks.getJSONObject(i);
            if ("text".equals(b.optString("type"))) out.append(b.optString("text"));
        }
        String text = out.toString().trim();
        if (text.isEmpty()) throw new Exception("Es kam keine Antwort. Versuche es mit weniger Text.");
        return text;
    }

    private static String read(InputStream in) throws Exception {
        if (in == null) return "";
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        byte[] b = new byte[8192];
        int n;
        while ((n = in.read(b)) > 0) buf.write(b, 0, n);
        in.close();
        return buf.toString("UTF-8");
    }
}
