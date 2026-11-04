// Kleiner Durchreicher für Such-Schnittstellen, die der Browser wegen CORS blockiert.
// Nur die unten erlaubten Adressen werden weitergeleitet – kein offener Proxy.
const ALLOWED = new Set([
  "mediathekviewweb.de", "archive.org", "api.dailymotion.com", "sepiasearch.org",
  "api.europeana.eu", "commons.wikimedia.org", "www.googleapis.com",
]);
const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers": "content-type",
};

export default async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  const ytKey = process.env.YOUTUBE_API_KEY || "";
  // Abfrage der Seite: Ist ein YouTube-Schlüssel in Netlify hinterlegt? (Der Schlüssel selbst bleibt geheim.)
  if (new URL(req.url).searchParams.get("check")) {
    return new Response(JSON.stringify({ yt: !!ytKey }), { headers: { ...CORS, "content-type": "application/json" } });
  }
  let target;
  try { target = new URL(new URL(req.url).searchParams.get("url")); } catch {
    return new Response("url fehlt", { status: 400, headers: CORS });
  }
  if (target.protocol !== "https:" || !ALLOWED.has(target.hostname)) {
    return new Response("Ziel nicht erlaubt", { status: 403, headers: CORS });
  }
  if (target.hostname === "www.googleapis.com" && !target.searchParams.get("key")) {
    if (!ytKey) return new Response("kein YouTube-Schlüssel hinterlegt", { status: 403, headers: CORS });
    target.searchParams.set("key", ytKey);
  }
  const init = { method: req.method, headers: { "user-agent": "roehrenkiste/1.0" } };
  if (req.method === "POST") {
    init.body = await req.text();
    init.headers["content-type"] = req.headers.get("content-type") || "text/plain";
  }
  // Referer weitergeben, damit ein auf die Seite beschränkter YouTube-Schlüssel funktioniert.
  const ref = req.headers.get("referer");
  if (ref) init.headers.referer = ref;
  const r = await fetch(target, init);
  return new Response(r.body, {
    status: r.status,
    headers: { ...CORS, "content-type": r.headers.get("content-type") || "application/json" },
  });
};
