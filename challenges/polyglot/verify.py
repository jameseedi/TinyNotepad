#!/usr/bin/env python3
"""Verify triptych.png is simultaneously a valid PNG, ZIP, and self-decoding
HTML source. The PNG and ZIP facets are checked here; the HTML/self-decode
facet is checked by confirming the pixels reconstruct renderer.js exactly
(the browser does the same read at runtime). Exit non-zero on any failure."""
import struct, zlib, sys, os, io, zipfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "triptych.png")
blob = open(F, "rb").read()
ok = True


def check(name, cond, extra=""):
    global ok
    ok = ok and cond
    print(("  ok  " if cond else " FAIL ") + name + ("  " + extra if extra else ""))


# --- PNG facet -------------------------------------------------------------
check("PNG signature", blob[:8] == b"\x89PNG\r\n\x1a\n")
im = Image.open(io.BytesIO(blob)); im.load()
check("PNG decodes", True, "%s %dx%d" % (im.mode, im.width, im.height))

# --- ZIP facet -------------------------------------------------------------
z = zipfile.ZipFile(io.BytesIO(blob))
check("ZIP opens & CRCs pass", z.testzip() is None, "entries=%s" % z.namelist())

# --- self-decode facet (what the browser reads at runtime) -----------------
rgb = im.convert("RGB").tobytes()   # raw R,G,B stream, exactly what canvas returns
n = struct.unpack(">I", rgb[:4])[0]
decoded = bytes(rgb[4:4 + n])
src = open(os.path.join(HERE, "renderer.js"), "rb").read()
check("pixels reconstruct renderer.js", decoded == src, "%d bytes" % n)

print("file size: %d bytes" % len(blob))
sys.exit(0 if ok else 1)
