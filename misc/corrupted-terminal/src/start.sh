#!/usr/bin/env bash
set -e
echo "[*] Building Corrupted Terminal Emulator..."
docker build -t corrupted-terminal .
echo "[*] Starting on port 7000..."
docker run --rm -p 7000:7000 --name corrupted-terminal corrupted-terminal
