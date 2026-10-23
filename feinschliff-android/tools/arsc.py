"""Minimal resources.arsc encoder: one package (0x7f) whose types each hold
file entries (e.g. xml/method -> res/xml/method.xml). Enough to point
manifest meta-data at compiled XML without aapt2."""

import struct

PKG_ID = 0x7F


def string_pool(strings, utf8=False):
    data, offsets = b"", []
    for s in strings:
        offsets.append(len(data))
        u = s.encode("utf-16-le")
        data += struct.pack("<H", len(s)) + u + b"\x00\x00"
    while len(data) % 4:
        data += b"\x00"
    start = 28 + 4 * len(strings)
    return (struct.pack("<HHIIIIII", 0x0001, 28, start + len(data), len(strings), 0, 0, start, 0)
            + b"".join(struct.pack("<I", o) for o in offsets) + data)


def encode(package_name, types):
    """types: list of (type_name, [(entry_name, file_path), ...]); ids are 0x7f TT EEEE in order."""
    values = [path for _, entries in types for _, path in entries]
    global_pool = string_pool(values)
    type_pool = string_pool([t for t, _ in types])
    keys = [name for _, entries in types for name, _ in entries]
    key_pool = string_pool(keys)

    chunks = b""
    vi = 0
    ki = 0
    for ti, (tname, entries) in enumerate(types, start=1):
        n = len(entries)
        chunks += struct.pack("<HHIBBHI", 0x0202, 16, 16 + 4 * n, ti, 0, 0, n) + b"\x00\x00\x00\x00" * n
        config = struct.pack("<I", 64) + b"\x00" * 60
        header_size = 20 + len(config)
        entries_start = header_size + 4 * n
        body = b""
        offs = []
        for name, path in entries:
            offs.append(len(body))
            body += struct.pack("<HHI", 8, 0, ki) + struct.pack("<HBBI", 8, 0, 0x03, vi)
            vi += 1
            ki += 1
        chunks += (struct.pack("<HHIBBHII", 0x0201, header_size, entries_start + len(body), ti, 0, 0, n, entries_start)
                   + config + b"".join(struct.pack("<I", o) for o in offs) + body)

    name16 = package_name.encode("utf-16-le")[:254].ljust(256, b"\x00")
    pkg_header = 288
    type_off = pkg_header
    key_off = type_off + len(type_pool)
    pkg = (struct.pack("<HHII", 0x0200, pkg_header, pkg_header + len(type_pool) + len(key_pool) + len(chunks), PKG_ID)
           + name16 + struct.pack("<IIIII", type_off, len(types), key_off, len(keys), 0)
           + type_pool + key_pool + chunks)
    content = global_pool + pkg
    return struct.pack("<HHII", 0x0002, 12, 12 + len(content), 1) + content
