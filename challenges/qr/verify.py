#!/usr/bin/env python3
"""Verify all three QRs decode to exactly what their builders encoded — the
same read a phone's decoder performs:
  program.qr.png  -> the well-formed vCard
  life.qr.png     -> the byte-exact data: URL program
  fragment.qr.png -> the rawcdn runner URL with the program in the #fragment,
                     which must decode back to the minified program
Whether the phone then acts on each (Add Contact / run the program) is OS or
browser behaviour we can't exercise headlessly. Exit non-zero on failure."""
import os, re, subprocess, sys, urllib.parse

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


# --- fragment.qr.png: program in the URL #fragment behind a hosted runner ---
def minify(html):
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"\s+", " ", html).strip()
    html = re.sub(r"\s+(?=\W)", "", html)
    html = re.sub(r"(?<=\W)\s+", "", html)
    return html


frag_url = scan("fragment.qr.png").rstrip("\n")
saved = open(os.path.join(HERE, "fragment.url.txt"), encoding="utf-8").read()
check("fragment QR round-trips byte-for-byte", frag_url == saved.rstrip("\n"))
check("points at the https rawcdn runner (no data: URL, so no mobile block)",
      frag_url.startswith("https://rawcdn.githack.com/") and "/run.html#" in frag_url)
program_in_frag = urllib.parse.unquote(frag_url.split("#", 1)[1])
program = minify(open(os.path.join(HERE, "life.html"), encoding="utf-8").read())
check("fragment decodes back to the minified program", program_in_frag == program,
      "%d program bytes carried in the QR" % len(program))
print("fragment QR: %d URL bytes (%d in the fragment)"
      % (len(frag_url), len(frag_url.split("#", 1)[1])))

sys.exit(0 if ok else 1)
