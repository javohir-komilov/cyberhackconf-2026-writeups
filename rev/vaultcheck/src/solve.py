import sys as _sys; _argv = _sys.argv[:]
from pwn import *

HOST = _argv[1] if len(_argv) > 1 else '127.0.0.1'
PORT = int(_argv[2]) if len(_argv) > 2 else 4448

context.log_level = 'error'

# The flag is derived by reversing the VM bytecode analysis.
# See write.md for the full derivation.
FLAG = b"CHC{v1rtu4l_m4ch1n3_r3v3rs3d}"

if HOST == 'LOCAL':
    p = process('./vaultcheck')
else:
    p = remote(HOST, PORT)

p.recvuntil(b'Password: ')
p.sendline(FLAG)
result = p.recvline(timeout=5).decode().strip()
print('[+]', result)
p.close()
