#!/usr/bin/env python3
"""Turn life.html into a scannable QR code that *is* the program.

The QR encodes a `data:text/html,...` URL containing a minified, fully
self-contained Conway's Game of Life. A phone QR scanner that opens data
URLs (most Android scanners, Google Lens) launches it straight into the
browser: a live simulation, no network, nothing installed. We keep the
payload small so the QR stays a low version and scans reliably off a screen
or print.

Outputs program.qr.png and prints the exact URL it encoded so it can be
round-trip decoded (see verify with zbarimg / the README)."""
import re, os, qrcode

HERE = os.path.dirname(os.path.abspath(__file__))


def minify(html):
    # strip HTML comments, then collapse all whitespace and drop every space
    # that isn't between two word characters. That removes the optional spaces
    # around JS/CSS punctuation (`= seed` -> `=seed`, `n == 3` -> `n==3`) while
    # preserving the mandatory ones (`function step`, `50 100`), so the source
    # stays readable but the payload — and the QR version — shrink hard.
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"\s+", " ", html).strip()
    html = re.sub(r"\s+(?=\W)", "", html)   # space before punctuation
    html = re.sub(r"(?<=\W)\s+", "", html)   # space after punctuation
    return html


def main():
    src = open(os.path.join(HERE, "life.html"), encoding="utf-8").read()
    program = minify(src)
    # data URL. In the data body only '%' (percent-encoding intro) and '#'
    # (fragment) are structural, so encode just those two — the browser
    # decodes them back before running the program (the JS uses '%' for its
    # toroidal wraparound modulo). Everything else browsers accept verbatim,
    # which keeps the payload short and the QR a low, scannable version.
    body = program.replace("%", "%25").replace("#", "%23")
    url = "data:text/html," + body

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # max capacity
        box_size=8, border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    out = os.path.join(HERE, "program.qr.png")
    img.save(out)

    # record the exact payload for round-trip verification / manual use
    with open(os.path.join(HERE, "program.url.txt"), "w") as f:
        f.write(url)

    print("program bytes: %d" % len(program))
    print("URL bytes:     %d" % len(url))
    print("QR version:    %d (%dx%d modules)" % (qr.version, qr.modules_count, qr.modules_count))
    print("wrote %s" % os.path.basename(out))


if __name__ == "__main__":
    main()
