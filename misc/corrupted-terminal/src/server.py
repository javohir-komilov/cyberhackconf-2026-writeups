#!/usr/bin/env python3
"""
Corrupted Terminal Emulator - CTF Challenge Server
Safe TCP server with virtual filesystem, no real OS access.
"""

import socketserver
import threading
import hashlib
import base64
import random
import string
import re
import time
import os

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
PORT            = 7000
SESSION_TIMEOUT = 120   # seconds
CMD_LIMIT       = 80
MAX_INPUT_LEN   = 100
INPUT_RE        = re.compile(r'^[a-zA-Z0-9._:\- ]+$')

# ──────────────────────────────────────────────
# FLAG ASSEMBLY  (never stored in plaintext here)
# ──────────────────────────────────────────────
_F1 = base64.b64decode("Q0hDe2MwcnJ1cHQzZF9zaA==").decode()  # CHC{c0rrupt3d_sh
_F2 = base64.b64decode("M2xsX3IzcDQxcjNkfQ==").decode()     # 3ll_r3p41r3d}
FLAG = os.getenv("FLAG", _F1 + _F2)   # reads from env if set (whale), else default

# ──────────────────────────────────────────────
# FIXED PUZZLE PARTS (deterministic, always solvable)
# ──────────────────────────────────────────────
PART_A = "t3rm1nal"
PART_B = "c0rrupt"
PART_C = "d_fx"

# key = md5(PART_A + PART_B)[:8] + PART_C
_expected_md5 = hashlib.md5((PART_A + PART_B).encode()).hexdigest()[:8]
UNLOCK_KEY = _expected_md5 + PART_C   # e.g. "e3b0c44d" + "d_fx"


# ──────────────────────────────────────────────
# HELPERS: encoding layers
# ──────────────────────────────────────────────

def text_to_octal_string(text: str) -> str:
    """Convert text → octal bytes, no separators, zero-padded to 3 digits."""
    return "".join(f"{b:03o}" for b in text.encode())


def octal_string_to_b64(text: str) -> str:
    """text → octal string → base64."""
    oct_str = text_to_octal_string(text)
    return base64.b64encode(oct_str.encode()).decode()


def text_to_binary_string(text: str) -> str:
    """text → binary string (8 bits per byte)."""
    return "".join(f"{b:08b}" for b in text.encode())


def md5hex(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


# ──────────────────────────────────────────────
# VIRTUAL FILESYSTEM
# ──────────────────────────────────────────────

# Real files (solvable)
REAL_FILES = {
    "readme.txt": (
        "Welcome to the CORRUPTED TERMINAL EMULATOR v0.9\n"
        "System integrity: 43%\n"
        "Some subsystems are damaged. Proceed with caution.\n"
        f"[HINT] Part A of the unlock key is encoded in kernel.log\n"
    ),
    "kernel.log": (
        "KERNEL PANIC at 0x00DEAD\n"
        f"Recovery token alpha: {PART_A}\n"
        "Stack trace:\n"
        "  #0  crash_handler()\n"
        "  #1  terminal_init()\n"
        "Checksum failed. Memory corrupted.\n"
    ),
    "sys.cfg": (
        "[system]\n"
        "mode=recovery\n"
        f"token_beta={PART_B}\n"
        "entropy=low\n"
        "watchdog=disabled\n"
    ),
    "unlock_guide.txt": (
        "KEY CONSTRUCTION PROTOCOL\n"
        "--------------------------\n"
        "Step 1: Obtain token_alpha from kernel.log  (Part A)\n"
        "Step 2: Obtain token_beta  from sys.cfg     (Part B)\n"
        "Step 3: Obtain suffix      from network.hex (Part C)\n"
        "Step 4: key = md5(A+B)[:8] + C\n"
        "Step 5: unlock <key>\n"
    ),
    "network.hex": (
        "RAW PACKET DUMP\n"
        "offset 0x00: ff fe 03 00\n"
        f"suffix_tag: {PART_C}\n"
        "offset 0x10: de ad be ef\n"
        "CRC: INVALID\n"
    ),
}

# Fake / decoy files
FAKE_FILES = {
    "flag.txt": (
        "CHC{fake_f14g_n0t_r341}\n"
        "Nice try. This is a decoy.\n"
    ),
    "backup.flag": (
        "BACKUP RECOVERY\n"
        "partial_key=t3rm1nalc0rru  <-- almost, but md5 won't match\n"
        "DO NOT USE\n"
    ),
    "debug.tmp": (
        "010110001001001001110100011010010000101001001101\n"
        "101001110010110100010110110100101011001010110100\n"
        "NO VALID MARKERS HERE. JUNK DATA.\n"
        "1110100110100010110001001001001110100011010\n"
    ),
    "shadow.bak": (
        "root:$6$FAKEHASH$nothinghere:19000:0:99999:7:::\n"
        "This is not real. System shadow file is inaccessible.\n"
    ),
}

ALL_FILES = {**REAL_FILES, **FAKE_FILES}

REAL_NAMES = list(REAL_FILES.keys())
FAKE_NAMES = list(FAKE_FILES.keys())
ALL_NAMES  = list(ALL_FILES.keys())


# ──────────────────────────────────────────────
# CAT output builders
# ──────────────────────────────────────────────

def noise_line(rng: random.Random) -> str:
    chars = "01" * 20 + "XYZABCDEF"
    return "".join(rng.choice(chars) for _ in range(rng.randint(30, 60)))


def build_cat_output(filename: str, content: str, rng: random.Random) -> str:
    """
    Encode content through layers and wrap with markers + noise.
    Layer: binary string, validated with md5.
    """
    lines = []

    # Header noise
    for _ in range(rng.randint(2, 4)):
        lines.append(f"# NOISE: {noise_line(rng)}")

    lines.append(f"# FILE: {filename}  CORRUPTION_LEVEL: {rng.randint(40,99)}%")
    lines.append("")

    # Binary layer
    bin_str = text_to_binary_string(content)
    lines.append("[B2-BEGIN]")
    # Split binary string into chunks of 64 for readability
    chunk_size = 64
    for i in range(0, len(bin_str), chunk_size):
        lines.append(bin_str[i:i+chunk_size])
    lines.append("[B2-END]")
    lines.append("")

    # MD5 of original content (validator)
    lines.append(f"[MD5] {md5hex(content)} [/MD5]")
    lines.append("")

    # Footer noise
    for _ in range(rng.randint(1, 3)):
        lines.append(f"# NOISE: {noise_line(rng)}")

    return "\n".join(lines) + "\n"


def build_cat_fake(filename: str, content: str, rng: random.Random) -> str:
    """Fake cat output: noise, broken binary, no valid md5."""
    lines = []
    for _ in range(rng.randint(3, 6)):
        lines.append(f"# NOISE: {noise_line(rng)}")
    lines.append(f"# FILE: {filename}  CORRUPTION_LEVEL: 100%")
    lines.append("[B2-BEGIN]")
    # Broken bits
    for _ in range(rng.randint(3, 6)):
        lines.append("".join(rng.choice("01X?") for _ in range(64)))
    lines.append("[B2-END]")
    lines.append(f"[MD5] {''.join(rng.choice('0123456789abcdef') for _ in range(32))} [/MD5]")
    for _ in range(rng.randint(1, 3)):
        lines.append(f"# NOISE: {noise_line(rng)}")
    return "\n".join(lines) + "\n"


# ──────────────────────────────────────────────
# SESSION
# ──────────────────────────────────────────────

class TerminalSession:
    def __init__(self, session_id: int):
        self.rng = random.Random(session_id)
        self.cmd_count = 0
        self.start_time = time.time()

    def expired(self) -> bool:
        return (time.time() - self.start_time) > SESSION_TIMEOUT

    def over_limit(self) -> bool:
        return self.cmd_count >= CMD_LIMIT

    def ls_output(self) -> str:
        """
        Encode all filenames with: text → octal string → base64
        Shuffle order per session.
        """
        names = ALL_NAMES[:]
        self.rng.shuffle(names)
        lines = ["Directory listing (encoded):"]
        for name in names:
            encoded = octal_string_to_b64(name)
            lines.append(f"  {encoded}")
        lines.append("")
        lines.append("Hint: each entry is base64(octal_bytes(filename))")
        return "\n".join(lines) + "\n"

    def cat_output(self, filename: str) -> str:
        rng2 = random.Random(hash(filename) ^ int(self.start_time))
        if filename in REAL_FILES:
            return build_cat_output(filename, REAL_FILES[filename], rng2)
        elif filename in FAKE_FILES:
            return build_cat_fake(filename, FAKE_FILES[filename], rng2)
        else:
            return f"cat: {filename}: No such file or directory\n"

    def handle(self, raw: str) -> str:
        self.cmd_count += 1
        line = raw.strip()

        if not line:
            return ""

        if not INPUT_RE.match(line):
            return "Error: invalid characters in input.\n"

        if len(line) > MAX_INPUT_LEN:
            return "Error: input too long.\n"

        parts = line.split(None, 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            return (
                "Available commands:\n"
                "  help           - this help\n"
                "  ls             - list files (encoded)\n"
                "  cat <file>     - display file contents (encoded)\n"
                "  status         - show system status\n"
                "  hint           - show a hint\n"
                "  unlock <key>   - unlock the system with a key\n"
                "  exit           - disconnect\n"
            )

        elif cmd == "ls":
            return self.ls_output()

        elif cmd == "cat":
            if not arg:
                return "Usage: cat <filename>\n"
            return self.cat_output(arg.strip())

        elif cmd == "status":
            elapsed = int(time.time() - self.start_time)
            remaining = max(0, SESSION_TIMEOUT - elapsed)
            return (
                f"System Status\n"
                f"  Integrity   : {self.rng.randint(10,50)}%\n"
                f"  Commands    : {self.cmd_count}/{CMD_LIMIT}\n"
                f"  Session time: {elapsed}s / {SESSION_TIMEOUT}s\n"
                f"  Time left   : {remaining}s\n"
                f"  Mode        : RECOVERY\n"
            )

        elif cmd == "hint":
            hints = [
                "ls output is base64 of octal bytes of the filename.",
                "Decode: b64decode → split into 3-digit groups → each group is octal → byte → ASCII.",
                "cat output has [B2-BEGIN]...[B2-END]: join all lines, group by 8 bits → bytes → ASCII.",
                "Validate with [MD5]: md5(decoded_text) should match the hash shown.",
                "Not all files are real. Some are decoys. The real key parts are in kernel.log, sys.cfg, network.hex.",
                "key = md5(partA + partB)[:8] + partC",
                "unlock <key> to get the flag.",
            ]
            return self.rng.choice(hints) + "\n"

        elif cmd == "unlock":
            if not arg:
                return "Usage: unlock <key>\n"
            if arg.strip() == UNLOCK_KEY:
                return f"\n*** ACCESS GRANTED ***\n\nFlag: {FLAG}\n\n"
            else:
                return "Access denied.\n"

        elif cmd == "exit":
            return "__EXIT__"

        else:
            return f"Unknown command: {cmd}\n"


# ──────────────────────────────────────────────
# TCP SERVER
# ──────────────────────────────────────────────

BANNER = r"""
  ██████╗ ██████╗ ██████╗ ██████╗ ██╗   ██╗██████╗ ████████╗███████╗██████╗
 ██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║   ██║██╔══██╗╚══██╔══╝██╔════╝██╔══██╗
 ██║     ██║   ██║██████╔╝██████╔╝██║   ██║██████╔╝   ██║   █████╗  ██║  ██║
 ██║     ██║   ██║██╔══██╗██╔══██╗██║   ██║██╔═══╝    ██║   ██╔══╝  ██║  ██║
 ╚██████╗╚██████╔╝██║  ██║██║  ██║╚██████╔╝██║        ██║   ███████╗██████╔╝
  ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝        ╚═╝   ╚══════╝╚═════╝
                    T E R M I N A L   E M U L A T O R   v 0 . 9
              [ SYSTEM INTEGRITY COMPROMISED - RECOVERY MODE ACTIVE ]

Type 'help' for available commands.
"""

_session_counter = 0
_counter_lock = threading.Lock()

def next_session_id() -> int:
    global _session_counter
    with _counter_lock:
        _session_counter += 1
        return _session_counter


class TerminalHandler(socketserver.StreamRequestHandler):
    def handle(self):
        sid = next_session_id()
        session = TerminalSession(sid)

        def send(msg: str):
            try:
                self.wfile.write(msg.encode())
                self.wfile.flush()
            except Exception:
                pass

        send(BANNER)
        send("terminal> ")

        try:
            while not session.expired() and not session.over_limit():
                self.connection.settimeout(SESSION_TIMEOUT)
                try:
                    raw = self.rfile.readline()
                except Exception:
                    break
                if not raw:
                    break

                line = raw.decode(errors="replace").rstrip("\r\n")
                response = session.handle(line)

                if response == "__EXIT__":
                    send("Goodbye.\n")
                    break

                if response:
                    send(response)

                if session.expired():
                    send("\nSession timeout. Disconnected.\n")
                    break
                if session.over_limit():
                    send("\nCommand limit reached. Disconnected.\n")
                    break

                send("terminal> ")

        except Exception:
            pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    host = "0.0.0.0"
    print(f"[*] Starting Corrupted Terminal Emulator on {host}:{PORT}")
    with ThreadedTCPServer((host, PORT), TerminalHandler) as srv:
        srv.serve_forever()
