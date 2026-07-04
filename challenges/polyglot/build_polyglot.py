#!/usr/bin/env python3
"""Build triptych.png: one file that is simultaneously a valid PNG, a valid
ZIP, and a valid HTML page whose own pixels are the JavaScript that renders
it. See README.md for the full write-up.

Layout of the output file:

    [PNG]   signature + IHDR + IDAT(pixels = renderer.js) + IEND
    [HTML]  <script> bootstrap: load self as <img>, read pixels, eval them
    [ZIP]   local headers + data + central directory + EOCD  (offsets fixed
            to account for the PNG+HTML prefix, so unzip finds everything)

PNG readers stop at IEND; ZIP readers scan from the EOCD at the very end;
an HTML parser ignores the binary and runs the <script>. Three formats,
one byte stream, no overlap tricks required beyond ordering.
"""
import struct, zlib, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "triptych.png")


# ---------------------------------------------------------------- PNG helpers
def chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def build_png(payload, width=96):
    """A color-type-2 (RGB, 8-bit) PNG whose pixel stream *is* `payload`.

    The first 4 pixels-worth of bytes hold the payload length (big-endian),
    then the payload bytes, then zero padding. Every scanline is stored with
    filter type 0 so a browser reading the pixels back off a <canvas> gets
    the bytes verbatim (opaque RGB round-trips losslessly through canvas;
    an alpha channel would not, due to premultiplication)."""
    body = struct.pack(">I", len(payload)) + payload
    stride = width * 3
    if len(body) % stride:
        body += b"\x00" * (stride - len(body) % stride)
    height = len(body) // stride

    raw = bytearray()
    for y in range(height):
        raw.append(0)                       # filter type: none
        raw += body[y * stride:(y + 1) * stride]

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png, width, height


# ---------------------------------------------------------------- ZIP writer
def zip_blob(files, prefix_len):
    """Minimal store-mode ZIP whose central-directory offsets are shifted by
    `prefix_len`, so the archive stays valid when concatenated after that
    many bytes of PNG+HTML."""
    local, central = bytearray(), bytearray()
    for name, data in files:
        nb = name.encode()
        crc = zlib.crc32(data) & 0xFFFFFFFF
        off = prefix_len + len(local)
        # local file header (method 0 = store)
        local += struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0, 0, 0, 0,
                             crc, len(data), len(data), len(nb), 0)
        local += nb + data
        # central directory header, offset adjusted for the prefix
        central += struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 20, 20, 0, 0,
                               0, 0, crc, len(data), len(data), len(nb),
                               0, 0, 0, 0, 0, off)
        central += nb
    cd_off = prefix_len + len(local)
    eocd = struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(files), len(files),
                       len(central), cd_off, 0)
    return bytes(local) + bytes(central) + eocd


# ---------------------------------------------------------------- bootstrap
# Kept terse but readable. Loads the file itself as an image, draws it to a
# canvas, reads the RGB back, pulls the length header then the JS bytes,
# hands the pixel data + source to the decoded program, and evals it.
BOOTSTRAP = (
    b"<!doctype html><meta charset=utf-8><title>triptych</title>"
    b"<body><script>"
    b"(function(){var i=new Image();i.crossOrigin='anonymous';i.onload=function(){"
    b"var c=document.createElement('canvas');c.width=i.width;c.height=i.height;"
    b"var g=c.getContext('2d');g.drawImage(i,0,0);"
    b"var d=g.getImageData(0,0,c.width,c.height).data,rgb=[];"
    b"for(var p=0;p<d.length;p+=4){rgb.push(d[p],d[p+1],d[p+2]);}"
    b"var n=(rgb[0]<<24|rgb[1]<<16|rgb[2]<<8|rgb[3])>>>0,b=[];"
    b"for(var k=0;k<n;k++)b.push(rgb[4+k]);"
    b"var s=new TextDecoder().decode(new Uint8Array(b));"
    b"window.__PX__={w:i.width,h:i.height,rgb:rgb};window.__SRC__=s;(0,eval)(s);"
    b"};i.onerror=function(){document.body.textContent='load the file over http:// to read its own pixels';};"
    b"i.src=location.href;})();"
    b"</script>\n"
)


def main():
    with open(os.path.join(HERE, "renderer.js"), "rb") as f:
        js = f.read()

    png, w, h = build_png(js)
    prefix = png + BOOTSTRAP

    files = [
        ("renderer.js", js),
        ("README.md", (
            "triptych.png is a PNG + ZIP + HTML polyglot.\n"
            "The PNG's pixels encode renderer.js (in this archive).\n"
            "Open it as HTML over http:// and the page decodes itself.\n"
        ).encode()),
    ]
    blob = prefix + zip_blob(files, len(prefix))

    with open(OUT, "wb") as f:
        f.write(blob)
    print("wrote %s: %d bytes, image %dx%d, JS %d bytes"
          % (os.path.basename(OUT), len(blob), w, h, len(js)))


if __name__ == "__main__":
    main()
