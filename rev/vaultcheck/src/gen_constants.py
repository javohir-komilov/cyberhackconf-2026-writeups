#!/usr/bin/env python3
"""
Generates the C constants embedded in vaultcheck.c:
  - Bytecode that checks the flag character-by-character in the VM
  - XOR-encrypted bytecode (using DEC_KEY)
  - DEC_KEY obfuscated with KEY_MASK
  - Obfuscated strings (XOR with STR_MASK)
"""

FLAG     = b"CHC{v1rtu4l_m4ch1n3_r3v3rs3d}"
assert len(FLAG) == 29, f"Expected 29, got {len(FLAG)}"

# ---- Opcodes ----
OP_PUSH = 0x01
OP_LOAD = 0x02
OP_XOR  = 0x03
OP_ADD  = 0x04
OP_SUB  = 0x09
OP_EQ   = 0x05
OP_AND  = 0x06
OP_HALT = 0x08

# ---- Generate bytecode ----
# Stack starts with [1].
# For each char: compute a transformed value and compare with expected.
# Three alternating patterns: XOR / ADD / SUB
bc = bytearray()
bc += bytes([OP_PUSH, 0x01])   # push 1 (initial success bit)

for i, c in enumerate(FLAG):
    t = i % 3
    if t == 0:
        # XOR check: LOAD i; PUSH k; XOR; PUSH exp; EQ; AND
        k   = (i * 17 + 31) & 0xFF
        exp = c ^ k
        bc += bytes([OP_LOAD, i, OP_PUSH, k, OP_XOR, OP_PUSH, exp, OP_EQ, OP_AND])
    elif t == 1:
        # ADD check: LOAD i; PUSH k; ADD; PUSH exp; EQ; AND
        k   = (i * 13 + 7) & 0xFF
        exp = (c + k) & 0xFF
        bc += bytes([OP_LOAD, i, OP_PUSH, k, OP_ADD, OP_PUSH, exp, OP_EQ, OP_AND])
    else:
        # SUB check: LOAD i; PUSH k; SUB; PUSH exp; EQ; AND
        k   = (i * 11 + 19) & 0xFF
        exp = (c - k) & 0xFF
        bc += bytes([OP_LOAD, i, OP_PUSH, k, OP_SUB, OP_PUSH, exp, OP_EQ, OP_AND])

bc += bytes([OP_HALT])

print(f"[*] Bytecode length : {len(bc)}")
print(f"[*] Flag length     : {len(FLAG)}")

# ---- Encrypt bytecode with rolling DEC_KEY ----
DEC_KEY = bytes([0x5a, 0x3f, 0x71, 0x2c, 0x8d, 0x4e, 0x91, 0xb2,
                 0x16, 0xd7, 0x4a, 0x23, 0x6f, 0x88, 0xc5, 0x37])
bc_enc = bytes([bc[i] ^ DEC_KEY[i % 16] for i in range(len(bc))])

# ---- Obfuscate DEC_KEY itself with KEY_MASK ----
KEY_MASK = 0xCA
key_enc = bytes([k ^ KEY_MASK for k in DEC_KEY])

# ---- Obfuscate strings with STR_MASK ----
STR_MASK = 0x55
s_prompt = bytes([c ^ STR_MASK for c in b"Password: "])
s_ok     = bytes([c ^ STR_MASK for c in b"Access granted."])
s_fail   = bytes([c ^ STR_MASK for c in b"Access denied."])

# ---- Verify round-trip ----
bc_decoded = bytes([bc_enc[i] ^ DEC_KEY[i % 16] for i in range(len(bc_enc))])
assert bc_decoded == bytes(bc), "Round-trip failed!"
print("[*] Bytecode round-trip OK")

# ---- Verify check logic ----
def simulate_vm(flag_bytes):
    """
    Simulate the VM.  Expected values (exp) come from FLAG (hardcoded in
    the bytecode), while the transformed value comes from flag_bytes (input).
    """
    acc = 1
    for i, c in enumerate(flag_bytes):
        fc  = FLAG[i]          # correct char (baked into bytecode)
        inp = flag_bytes[i]    # actual input char
        t   = i % 3
        if t == 0:
            k   = (i * 17 + 31) & 0xFF
            exp = fc  ^ k
            got = inp ^ k
        elif t == 1:
            k   = (i * 13 + 7)  & 0xFF
            exp = (fc  + k) & 0xFF
            got = (inp + k) & 0xFF
        else:
            k   = (i * 11 + 19) & 0xFF
            exp = (fc  - k) & 0xFF
            got = (inp - k) & 0xFF
        acc &= (1 if got == exp else 0)
    return acc

assert simulate_vm(FLAG) == 1, "VM simulation failed on correct flag!"
assert simulate_vm(b"A" * 29) == 0, "VM simulation should fail on wrong input!"
print("[*] VM simulation OK — correct flag passes, wrong input fails")

# ---- Helper ----
def c_arr(name, ty, data):
    vals = ", ".join(f"0x{b:02x}" for b in data)
    return f"static const {ty} {name}[] = {{{vals}}};"

# ---- Output C snippets ----
print()
print("/* --- paste into vaultcheck.c --- */")
print(f"#define EXPECTED_LEN  {len(FLAG)}")
print(f"#define BC_LEN        {len(bc)}")
print(f"#define KEY_MASK      0x{KEY_MASK:02x}")
print(f"#define STR_MASK      0x{STR_MASK:02x}")
print()
print(c_arr("key_enc",  "uint8_t", key_enc))
print(c_arr("bc_enc",   "uint8_t", bc_enc))
print(c_arr("s_prompt", "uint8_t", s_prompt))
print(c_arr("s_ok",     "uint8_t", s_ok))
print(c_arr("s_fail",   "uint8_t", s_fail))
