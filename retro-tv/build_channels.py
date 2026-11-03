#!/usr/bin/env python3
"""Erzeugt channels.js für die Röhrenkiste – nur nötig, falls der Browser die
Mediathek-Suche direkt blockiert (CORS) oder du die Liste offline haben willst.

Aufruf:  python3 build_channels.py
Danach index.html öffnen; die Seite nimmt channels.js automatisch als Rückfall.
Die Kanäle stehen unten in CHANNEL_DEFS (gleiche Bedeutung wie in index.html).
"""
import json
import urllib.request
from datetime import datetime, timezone

API = "https://mediathekviewweb.de/api/query"

CHANNEL_DEFS = [
    {"name": "ARD Retro",       "query": "ARD Retro|Retro",                "minMin": 5},
    {"name": "Zeitgeschichte",  "query": "Zeitreise|Damals|Archivschätze", "minMin": 10},
    {"name": "DDR-Fernsehen",   "query": "DDR-Fernsehen|DFF|Ostalgie",     "minMin": 10},
    {"name": "Krimi-Klassiker", "query": "Stahlnetz|Der Kommissar|Polizeiruf 110", "minMin": 40},
    {"name": "Kinderprogramm",  "query": "Sandmännchen|Augsburger Puppenkiste|Löwenzahn", "minMin": 5},
]


def search(query, min_min):
    body = {
        "queries": [{"fields": ["topic", "title"], "query": query}],
        "sortBy": "timestamp", "sortOrder": "asc", "future": False,
        "duration_min": min_min * 60, "offset": 0, "size": 200,
    }
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "text/plain", "User-Agent": "roehrenkiste/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("err"):
        raise RuntimeError(data["err"])
    out = []
    for x in data["result"]["results"]:
        url = (x.get("url_video_hd") or x.get("url_video") or "").replace("http:", "https:", 1)
        if not url or ".m3u8" in url or not x.get("duration"):
            continue
        topic, title = x.get("topic") or "", x.get("title") or ""
        ts = x.get("timestamp")
        out.append({
            "title": f"{topic}: {title}" if topic and topic != title else title,
            "url": url,
            "duration": int(x["duration"]),
            "year": datetime.fromtimestamp(ts, timezone.utc).year if ts else "",
            "desc": f"{x.get('channel', '')} · {x.get('description') or ''}",
        })
    return out


def main():
    channels = []
    for d in CHANNEL_DEFS:
        seen, items = set(), []
        for q in d["query"].split("|"):
            try:
                for it in search(q.strip(), d.get("minMin", 0)):
                    if it["url"] not in seen:
                        seen.add(it["url"])
                        items.append(it)
            except Exception as e:  # einzelne Suche darf scheitern
                print(f"  ! Suche '{q}' fehlgeschlagen: {e}")
        print(f"{d['name']}: {len(items)} Sendungen")
        channels.append({"name": d["name"], "items": items})
    with open("channels.js", "w", encoding="utf-8") as f:
        f.write("window.CHANNELS = " + json.dumps(channels, ensure_ascii=False) + ";\n")
    print("channels.js geschrieben.")


if __name__ == "__main__":
    main()
