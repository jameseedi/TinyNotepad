#!/usr/bin/env python3
"""Build life.qr.png: a QR whose payload *is* an entire program — a minified,
self-contained Conway's Game of Life, encoded as a `data:text/html,...` URL.

Where this runs, scanning it opens a live, full-screen simulation with no
network and nothing installed. WHERE IT DOESN'T: modern *mobile* browsers
block top-level navigation to `data:` URLs (you get `about:blank#blocked`),
so a cold scan on a stock phone won't launch it. It does run when the data
URL reaches a permissive context — desktop Firefox, some QR apps with their
own webview, or anywhere you can open a `data:` URL directly.

This is the "program literally inside the QR" variant, kept alongside the
vCard QR (build_qr.py) that every phone acts on offline. Same life.html
source feeds both."""
import re, os, qrcode

HERE = os.path.dirname(os.path.abspath(__file__))


def minify(html):
    # strip HTML comments, then collapse all whitespace and drop every space
    # that isn't between two word characters. That removes the optional spaces
    # around JS/CSS punctuation (`= seed` -> `=seed`, `n == 3` -> `n==3`) while
    # preserving the mandatory ones (`function step`), so the source stays
    # readable but the payload — and the QR version — shrink hard.
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"\s+", " ", html).strip()
    html = re.sub(r"\s+(?=\W)", "", html)   # space before punctuation
    html = re.sub(r"(?<=\W)\s+", "", html)   # space after punctuation
    return html


def main():
    src = open(os.path.join(HERE, "life.html"), encoding="utf-8").read()
    program = minify(src)
    # In the data body only '%' (percent-encoding intro) and '#' (fragment)
    # are structural; encode just those two — the browser decodes them back
    # before running the program (the JS uses '%' for its toroidal modulo).
    body = program.replace("%", "%25").replace("#", "%23")
    url = "data:text/html," + body

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=8, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(
        os.path.join(HERE, "life.qr.png"))

    with open(os.path.join(HERE, "life.url.txt"), "w") as f:
        f.write(url)

    print("program bytes: %d" % len(program))
    print("URL bytes:     %d" % len(url))
    print("QR version:    %d (%dx%d modules, ECC level L)"
          % (qr.version, qr.modules_count, qr.modules_count))
    print("wrote life.qr.png  (runs where data: URLs are permitted)")


if __name__ == "__main__":
    main()
