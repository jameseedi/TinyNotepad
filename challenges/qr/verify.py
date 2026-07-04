#!/usr/bin/env python3
"""Verify both QRs decode to exactly what their builders encoded — the same
read a phone's decoder performs. program.qr.png must be the well-formed
vCard; life.qr.png must be the byte-exact data: URL. Whether the phone then
offers "Add Contact" (vCard) or runs the program (data: URL, browser-
dependent) are behaviours we can't exercise headlessly. Exit non-zero on
failure."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ok = True


def check(name, cond, extra=""):
    global ok
    ok = ok and cond
    print(("  ok  " if cond else " FAIL ") + name + ("  " + extra if extra else ""))


def scan(name):
    return subprocess.check_output(
        ["zbarimg", "--quiet", "--raw", os.path.join(HERE, name)]).decode("utf-8")


# --- program.qr.png: the vCard --------------------------------------------
decoded = scan("program.qr.png")
payload = open(os.path.join(HERE, "program.payload.txt"), encoding="utf-8").read()
# normalise line endings (zbar emits LF; the payload is CRLF per spec)
norm = lambda s: s.replace("\r\n", "\n").rstrip("\n")
check("vCard QR decodes to the payload", norm(decoded) == norm(payload))
lines = norm(decoded).split("\n")
check("starts BEGIN:VCARD", lines[0] == "BEGIN:VCARD")
check("ends END:VCARD", lines[-1] == "END:VCARD")
check("declares VERSION:3.0", "VERSION:3.0" in lines)
for field in ("N:", "FN:", "EMAIL", "URL:", "NOTE:"):
    check("vCard has %s" % field, any(l.split(":", 1)[0].startswith(field.rstrip(":"))
                                      for l in lines))
print("vCard: %d bytes, %d fields" % (len(payload), len(lines)))

# --- life.qr.png: the data: URL program -----------------------------------
life = scan("life.qr.png")
life_url = open(os.path.join(HERE, "life.url.txt"), encoding="utf-8").read()
check("life QR round-trips byte-for-byte", life.rstrip("\n") == life_url.rstrip("\n"))
check("life payload is a data:text/html program",
      life_url.startswith("data:text/html,") and "<script>" in life_url,
      "%d bytes" % len(life_url))

sys.exit(0 if ok else 1)
