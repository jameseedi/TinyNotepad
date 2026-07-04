#!/usr/bin/env python3
"""Verify program.qr.png decodes to the exact vCard payload and that the
vCard is well formed. This is the same read a phone's decoder performs;
whether the phone then offers "Add Contact" is an OS behaviour we can't
exercise headlessly, but the payload is the standard vCard 3.0 that every
mobile camera recognises. Exit non-zero on failure."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ok = True


def check(name, cond, extra=""):
    global ok
    ok = ok and cond
    print(("  ok  " if cond else " FAIL ") + name + ("  " + extra if extra else ""))


# decode the QR exactly as a scanner would
raw = subprocess.check_output(
    ["zbarimg", "--quiet", "--raw", os.path.join(HERE, "program.qr.png")])
decoded = raw.decode("utf-8")

payload = open(os.path.join(HERE, "program.payload.txt"), encoding="utf-8").read()

# normalise line endings (zbar emits LF; the payload is CRLF per spec) and
# ignore a trailing blank line
norm = lambda s: s.replace("\r\n", "\n").rstrip("\n")
check("QR decodes to the payload", norm(decoded) == norm(payload))

lines = norm(decoded).split("\n")
check("starts BEGIN:VCARD", lines[0] == "BEGIN:VCARD")
check("ends END:VCARD", lines[-1] == "END:VCARD")
check("declares VERSION:3.0", "VERSION:3.0" in lines)
for field in ("N:", "FN:", "EMAIL", "URL:", "NOTE:"):
    check("has %s" % field, any(l.startswith(field) or field in l.split(":", 1)[0]
                                for l in lines))

print("payload: %d bytes, %d fields" % (len(payload), len(lines)))
sys.exit(0 if ok else 1)
