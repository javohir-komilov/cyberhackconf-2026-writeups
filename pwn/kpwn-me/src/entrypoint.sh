#!/bin/sh
set -e

# Rebuild initramfs with the dynamic flag injected by whale (FLAG=24-char-hex)
WORK=$(mktemp -d)
cd "$WORK"
gunzip -c /home/pwn/initramfs.cpio.gz | cpio -id 2>/dev/null

# Write dynamic flag: whale injects FLAG env var as 24-char hex
printf 'CHC{kpwn_me_%s}\n' "${FLAG}" > flag
chmod 400 flag

# Repack with root ownership preserved
find . | cpio -o -H newc 2>/dev/null | gzip > /home/pwn/initramfs-live.cpio.gz

cd /
rm -rf "$WORK"

# Serve via socat — each connection spawns its own QEMU instance
exec socat -T300 TCP-LISTEN:1337,reuseaddr,fork EXEC:/home/pwn/run-live.sh,stderr
