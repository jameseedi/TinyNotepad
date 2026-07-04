#!/bin/sh
# Assemble tinypad.exe and enforce the size budget.
set -e
fasm tinypad.asm tinypad.exe
size=$(stat -c%s tinypad.exe 2>/dev/null || stat -f%z tinypad.exe)
echo "tinypad.exe: ${size} bytes (budget: 2048)"
if [ "$size" -ge 2048 ]; then
    echo "FAIL: over the 2 KiB budget" >&2
    exit 1
fi
