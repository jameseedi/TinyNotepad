#!/usr/bin/env python3
"""Build program.qr.png: a QR the plain phone camera reliably *acts on*,
offline, with no browser and no taps into a blocked page.

Earlier this challenge encoded a whole program as a `data:text/html` URL.
That decodes fine, but every modern mobile browser blocks *top-level
navigation* to `data:` URLs for security (you get `about:blank#blocked`),
so scanning it never runs the program on a stock phone. See README.md.

So the QR now carries a **vCard** — the structured payload phones treat as
an action. Scan it with the built-in camera (iOS Camera, Android, Google
Lens all recognise vCards) and the phone offers to create a fully populated
contact: name, org, title, email, url, and a note. Non-trivial, offline,
and it works on any phone with no app to install.

The program that used to live in the QR still lives in this folder as
life.html — open it in a browser (or host it) to run the Game of Life."""
import os, qrcode

HERE = os.path.dirname(os.path.abspath(__file__))

# vCard 3.0. Spec line ending is CRLF; parsers on phones expect it.
VCARD = "\r\n".join([
    "BEGIN:VCARD",
    "VERSION:3.0",
    "N:exe;tinypad;;;",
    "FN:tinypad.exe",
    "ORG:TinyNotepad",
    "TITLE:A usable Win32 notepad in 921 bytes",
    "EMAIL;TYPE=INTERNET:hello@example.com",
    "URL:https://github.com/jameseedi/tinynotepad",
    "NOTE:You created this contact by pointing a camera at a QR code — "
    "proof a QR can do something non-trivial, offline, on any phone.",
    "END:VCARD",
    "",
])


def main():
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # M: sturdier scan
        box_size=8, border=4,
    )
    qr.add_data(VCARD)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(
        os.path.join(HERE, "program.qr.png"))

    with open(os.path.join(HERE, "program.payload.txt"), "w", newline="") as f:
        f.write(VCARD)

    print("payload bytes: %d" % len(VCARD))
    print("QR version:    %d (%dx%d modules, ECC level M)"
          % (qr.version, qr.modules_count, qr.modules_count))
    print("wrote program.qr.png")


if __name__ == "__main__":
    main()
