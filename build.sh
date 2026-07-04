#!/bin/sh
# Assemble both editors and enforce their size budgets.
set -e

check() { # file budget
    size=$(stat -c%s "$1" 2>/dev/null || stat -f%z "$1")
    echo "$1: ${size} bytes (budget: $2)"
    if [ "$size" -ge "$2" ]; then
        echo "FAIL: $1 over budget" >&2
        exit 1
    fi
}

fasm tinypad.asm tinypad.exe
check tinypad.exe 2048

fasm micropad.asm micropad.exe
check micropad.exe 768
