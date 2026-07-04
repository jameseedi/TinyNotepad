#!/usr/bin/env python3
"""Build fragment.qr.png: a QR that runs a real program on ANY phone.

The QR encodes an https URL to a fixed, generic runner (run.html, served
from this repo via raw.githack) with the program carried in the URL
#fragment:

    https://raw.githack.com/USER/REPO/REF/challenges/qr/run.html#<program>

Scanning it navigates to plain https (allowed on every phone — no data: URL,
so no `about:blank#blocked`), and run.html reads the fragment and writes it
out as the document. The fragment is never sent to the server, so the
program stays on the device: it genuinely lives in the QR you scanned.

The runner URL is pinned to a commit SHA so it's immutable and permanently
cacheable. Regenerate RUNNER_URL's SHA if run.html ever changes; see the
README for the two-commit dance."""
import re, os, urllib.parse, qrcode

HERE = os.path.dirname(os.path.abspath(__file__))

# Pinned to the commit that introduced run.html (immutable, CDN-cacheable).
RUNNER_URL = "https://rawcdn.githack.com/jameseedi/tinynotepad/8cf52646553c0bd9b07c7b45f2072b75006bb115/challenges/qr/run.html"


def minify(html):
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"\s+", " ", html).strip()
    html = re.sub(r"\s+(?=\W)", "", html)
    html = re.sub(r"(?<=\W)\s+", "", html)
    return html


def main():
    program = minify(open(os.path.join(HERE, "life.html"), encoding="utf-8").read())
    # match JS encodeURIComponent: leave its unreserved set unescaped
    frag = urllib.parse.quote(program, safe="!*'()-._~")
    url = RUNNER_URL + "#" + frag

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=8, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(
        os.path.join(HERE, "fragment.qr.png"))

    with open(os.path.join(HERE, "fragment.url.txt"), "w") as f:
        f.write(url)

    print("program bytes:  %d" % len(program))
    print("fragment bytes: %d" % len(frag))
    print("URL bytes:      %d" % len(url))
    print("QR version:     %d (%dx%d modules, ECC level L)"
          % (qr.version, qr.modules_count, qr.modules_count))
    print("runner: %s" % RUNNER_URL)
    if "__SHA__" in RUNNER_URL:
        print("WARNING: RUNNER_URL still has the __SHA__ placeholder")


if __name__ == "__main__":
    main()
