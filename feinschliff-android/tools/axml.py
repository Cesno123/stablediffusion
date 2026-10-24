"""Minimal binary AndroidManifest (AXML) encoder.

Encodes a small element tree into Android's compiled XML format: string pool
(UTF-16), resource-id map for android: attributes, namespace and element
chunks. Enough for a manifest without app resources.
"""

import struct

ANDROID_NS = "http://schemas.android.com/apk/res/android"

# android.R.attr ids (read from the framework jar with javap)
ATTR_IDS = {
    "theme": 0x01010000, "label": 0x01010001, "icon": 0x01010002, "name": 0x01010003,
    "exported": 0x01010010, "taskAffinity": 0x01010012, "excludeFromRecents": 0x01010017,
    "mimeType": 0x01010026, "minSdkVersion": 0x0101020C, "versionCode": 0x0101021B,
    "versionName": 0x0101021C, "windowSoftInputMode": 0x0101022B, "targetSdkVersion": 0x01010270,
    "allowBackup": 0x01010280, "permission": 0x01010006, "resource": 0x01010025,
    "settingsActivity": 0x01010225, "supportsSwitchingToNextInputMethod": 0x010103EB,
    "authorities": 0x01010018, "grantUriPermissions": 0x0101001B,
}

T_REFERENCE, T_STRING, T_INT_DEC, T_INT_HEX, T_BOOLEAN = 0x01, 0x03, 0x10, 0x11, 0x12


class Ref(int):
    """An @android: resource reference (e.g. a framework theme or drawable)."""


class Hex(int):
    """An integer flag value written as hex (e.g. windowSoftInputMode)."""


def E(tag, attrs=None, *children):
    return (tag, attrs or {}, list(children))


def encode(root):
    # collect strings: android attribute names first (they need the resource map), then the rest
    android_attrs, other = [], []

    def walk(node):
        tag, attrs, children = node
        for k, v in attrs.items():
            ns, _, name = k.rpartition(":")
            (android_attrs if ns == "android" else other).append(name)
            if isinstance(v, str):
                other.append(v)
        other.append(tag)
        for c in children:
            walk(c)

    walk(root)
    strings = sorted(set(android_attrs), key=lambda n: ATTR_IDS[n])  # must lead the pool, in resource-map order
    n_res = len(strings)
    for s in ["android", ANDROID_NS] + other:
        if s not in strings:
            strings.append(s)
    idx = {}
    for i, s in enumerate(strings):
        idx.setdefault(s, i)

    def sidx(s):
        return idx[s]

    # string pool (UTF-16)
    data = b""
    offsets = []
    for s in strings:
        offsets.append(len(data))
        u = s.encode("utf-16-le")
        data += struct.pack("<H", len(s)) + u + b"\x00\x00"
    while len(data) % 4:
        data += b"\x00"
    header_size = 28
    strings_start = header_size + 4 * len(strings)
    pool = struct.pack("<HHIIIIII", 0x0001, header_size, strings_start + len(data), len(strings), 0, 0, strings_start, 0)
    pool += b"".join(struct.pack("<I", o) for o in offsets) + data

    resmap = struct.pack("<HHI", 0x0180, 8, 8 + 4 * n_res) + b"".join(
        struct.pack("<I", ATTR_IDS[strings[i]]) for i in range(n_res))

    body = []
    ns_prefix, ns_uri = sidx("android"), sidx(ANDROID_NS)
    body.append(struct.pack("<HHIIiII", 0x0100, 16, 24, 1, -1, ns_prefix, ns_uri))

    def element(node):
        tag, attrs, children = node
        enc = []
        for k, v in attrs.items():
            ns, _, name = k.rpartition(":")
            ns_i = ns_uri if ns == "android" else 0xFFFFFFFF
            name_i = sidx(name)
            if isinstance(v, str):
                raw, typ, val = sidx(v), T_STRING, sidx(v)
            elif isinstance(v, bool):
                raw, typ, val = 0xFFFFFFFF, T_BOOLEAN, 0xFFFFFFFF if v else 0
            elif isinstance(v, Ref):
                raw, typ, val = 0xFFFFFFFF, T_REFERENCE, int(v)
            elif isinstance(v, Hex):
                raw, typ, val = 0xFFFFFFFF, T_INT_HEX, int(v)
            else:
                raw, typ, val = 0xFFFFFFFF, T_INT_DEC, int(v)
            sort_key = ATTR_IDS.get(name, 0xFFFFFFFF) if ns == "android" else 0x7FFFFFFF
            enc.append((sort_key, struct.pack("<IIIHBBI", ns_i, name_i, raw, 8, 0, typ, val)))
        enc.sort(key=lambda e: e[0])  # attributes ordered by resource id, as aapt does
        attr_bytes = b"".join(e[1] for e in enc)
        size = 16 + 20 + len(attr_bytes)
        body.append(struct.pack("<HHIIi", 0x0102, 16, size, 1, -1)
                    + struct.pack("<IIHHHHHH", 0xFFFFFFFF, sidx(tag), 20, 20, len(enc), 0, 0, 0) + attr_bytes)
        for c in children:
            element(c)
        body.append(struct.pack("<HHIIiII", 0x0103, 16, 24, 1, -1, 0xFFFFFFFF, sidx(tag)))

    element(root)
    body.append(struct.pack("<HHIIiII", 0x0101, 16, 24, 1, -1, ns_prefix, ns_uri))
    content = pool + resmap + b"".join(body)
    return struct.pack("<HHI", 0x0003, 8, 8 + len(content)) + content
