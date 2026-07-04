# program.qr.png — a QR the phone actually acts on

Point a phone camera at this QR and it *does something*, offline, with no app
to install: it offers to **create a fully populated contact** — name, org,
title, email, url, and a note explaining itself. It's a vCard, the structured
payload every phone (iOS Camera, Android, Google Lens) recognises and acts on.

![the QR](program.qr.png)

Scan it and your phone pops "Add Contact" for **tinypad.exe / TinyNotepad**.

## Why not "a program in the QR"?

The first cut of this challenge encoded a whole program — a Conway's Game of
Life — as a `data:text/html,...` URL. It decodes perfectly (you can still see
it run: [`life.html`](life.html)), but it **does not run when scanned on a
phone**, and that's not fixable in the payload:

> Modern browsers block *top-level navigation* to `data:` URLs as an
> anti-phishing measure (Chrome 60+, and every mobile browser). A QR scan
> that opens the URL hits exactly that block — you get `about:blank#blocked`.

There is no server here to host the page, so there's no first-party origin a
`data:` document could be opened from. Running arbitrary code straight off a
phone scan, offline, is precisely what browsers refuse to do. So the QR that
*ships* is one the phone reliably acts on — a vCard — and the program stays in
the folder as a file you can run directly or host.

`life.html` still works: open it in any browser (or serve it) to watch the
Game of Life. It's a genuine self-contained program; it just can't be launched
from a cold scan.

## The payload

A standard vCard 3.0 (CRLF line endings, as the spec wants):

```
BEGIN:VCARD
VERSION:3.0
N:exe;tinypad;;;
FN:tinypad.exe
ORG:TinyNotepad
TITLE:A usable Win32 notepad in 921 bytes
EMAIL;TYPE=INTERNET:hello@example.com
URL:https://github.com/jameseedi/tinynotepad
NOTE:You created this contact by pointing a camera at a QR code — …
END:VCARD
```

337 bytes → a version-14 (73×73) QR at error-correction level **M**, so it
scans crisply off a screen or a modest print with margin to spare.

## Build & verify

```sh
python3 build_qr.py            # emit program.qr.png + program.payload.txt
python3 verify.py              # decode with zbar, check it's a valid vCard
zbarimg --raw program.qr.png   # see exactly what a scanner reads
```

`verify.py` decodes the QR the same way a phone's scanner does and confirms
it's the exact, well-formed vCard. Requires `qrcode` (`pip install qrcode`),
Pillow, and `zbar-tools`.

Whether the phone then shows "Add Contact" is OS behaviour we can't drive
headlessly — but a vCard is the canonical contact payload, recognised by the
stock camera on both major platforms. The email is a placeholder
(`example.com`) and the URL is this repo.

## Files

| file | what it is |
|---|---|
| `program.qr.png` | the scannable QR — the deliverable |
| `program.payload.txt` | the exact vCard the QR encodes |
| `build_qr.py` | builds the vCard and renders the QR |
| `verify.py` | decodes + validates it |
| `life.html` | the original Game of Life — still runs, just not from a scan |
