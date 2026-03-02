#!/usr/bin/env python3
import sys

BANNED = [
    'import', 'open', 'os', 'exec', 'eval',
    'system', 'popen', 'subprocess',
    'breakpoint', 'compile',
    # block trivial getattr / builtins access → forces MRO path
    'getattr', 'setattr', '__builtins__', 'builtins',
    'globals', 'vars', 'locals', '__import__',
]

def main():
    sys.stdout.write("=== PyJail v1 ===\n")
    sys.stdout.write("Some builtins have been blocked. Flag is in flag.txt.\n")
    sys.stdout.flush()
    while True:
        sys.stdout.write(">>> ")
        sys.stdout.flush()
        line = sys.stdin.readline()
        if not line:
            break
        line = line.rstrip('\n').rstrip('\r')
        if not line:
            continue

        blocked = False
        for word in BANNED:
            if word in line:
                sys.stdout.write(f"[!] '{word}' is blocked.\n")
                sys.stdout.flush()
                blocked = True
                break

        if not blocked:
            try:
                result = eval(line, {"__builtins__": __builtins__}, {})
                if result is not None:
                    sys.stdout.write(repr(result) + '\n')
                    sys.stdout.flush()
            except Exception as e:
                sys.stdout.write(f"[!] {type(e).__name__}: {e}\n")
                sys.stdout.flush()

if __name__ == '__main__':
    main()
