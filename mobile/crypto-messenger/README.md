# CryptoMessenger

| Field | Value |
|-------|-------|
| Category | Mobile |
| Points | ? |

## Description

> A suspicious Android messaging app has been intercepted.
> It uses custom encryption for its communications.
> Reverse engineer the APK to recover the hidden flag.

## Solution

# CryptoMessenger CTF — Writeup

> **Challenge:** CryptoMessenger  
> **Difficulty:** Medium-Hard  
> **Category:** Android Reverse Engineering

---

## Challenge Description

> *CryptoMessenger — xavfsiz messenger ilovasi. Ilovadagi maxfiy xabarni toping.*  
> **Flag formati:** `CHC{...}`

Bizga `CryptoMessenger.apk` fayl berilgan. Ilova oddiy ko'rinishda — login ekrani va chat ro'yxati. Lekin ichida maxfiy xabar yashiringan. Uni topish uchun **3 bosqichdan** o'tishimiz kerak.

---

## Bosqich 1: APK Static Analysis — API Key Topish

### 1.1 APK ni decompile qilish

Birinchi qadam — APK ni decompile qilib, source kodini o'qish. Buning uchun **JADX** toolidan foydalanamiz:

```bash
jadx CryptoMessenger.apk -d output/
```

### 1.2 AndroidManifest.xml ni tahlil qilish

Har doim birinchi qarab chiqadigan fayl — `AndroidManifest.xml`. Bu faylda ilovaning barcha komponentlari ro'yxatga olingan.

```xml
<activity
    android:name=".SecretChatActivity"
    android:exported="true">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data
            android:scheme="msgr"
            android:host="chat"
            android:pathPrefix="/secret" />
    </intent-filter>
</activity>
```

> [!IMPORTANT]
> `SecretChatActivity` **exported="true"** va deep link qabul qiladi: `msgr://chat/secret`. Bu juda qiziqarli!

### 1.3 SecretChatActivity source codini o'qish

JADX orqali `SecretChatActivity.java` ni ochsak, quyidagilarni ko'ramiz:

```java
public class SecretChatActivity extends AppCompatActivity {
    public native String a(byte[] d);
    public native byte[] b();
    public native int c(String k);

    protected void onCreate(Bundle savedInstanceState) {
        // ...
        Uri uri = getIntent().getData();
        String k = uri.getQueryParameter("k");
        
        int r = c(k);    // "k" parametrni tekshiradi
        if (r != 1) {
            // Access Denied
            return;
        }
        
        byte[] enc = b();      // Shifrlangan data oladi
        String decoded = a(enc); // Decode qiladi
        // Base64 ga encode qilib ko'rsatadi
    }
}
```

**Xulosa:** Deep link `k` parametr talab qiladi. Bu parametr native `c()` funksiyasi orqali tekshiriladi. To'g'ri key bilan `b()` funksiyasi maxfiy xabarni qaytaradi.

### 1.4 API Key ni topish

Endi savollar: bu `k` parametrga qanday qiymat berish kerak?

`strings.xml` faylini ko'rib chiqamiz:

```xml
<string name="build_id">Y1I3bVg5cEwya1E0</string>
```

`build_id` — oddiy ko'rinishda build identifikatori, lekin aslida Base64 ga o'xshaydi! Decode qilib ko'ramiz:

```bash
echo "Y1I3bVg5cEwya1E0" | base64 -d
```

**Natija:**
```
cR7mX9pL2kQ4
```

Bu bizning API key!

---

## Bosqich 2: Deep Link Exploitation — Maxfiy Chatga Kirish

Endi topilgan API key ni deep link bilan ishlatamiz. `AndroidManifest.xml` dan bildikki, deep link sxemasi `msgr://chat/secret`, va `SecretChatActivity` kodidan `k` parametr kerakligini bilamiz.

### 2.1 ADB orqali deep link yuborish

```bash
adb shell am start -a android.intent.action.VIEW \
    -d "msgr://chat/secret?k=cR7mX9pL2kQ4"
```

### 2.2 Natija

Agar API key to'g'ri bo'lsa, ekranda **"Channel Unlocked"** yozuvi va quyidagi Base64 string chiqadi:

```
Q0hDe2QzM3BfbDFua19jaDQxbl90MF9uNHQxdjNfcjN2M3JzM30=
```

Bu Base64 encoded flag! Decode qilamiz:

```bash
echo "Q0hDe2QzM3BfbDFua19jaDQxbl90MF9uNHQxdjNfcjN2M3JzM30=" | base64 -d
```
---

**Natija:**
```
CHC{d33p_l1nk_ch41n_t0_n4t1v3_r3v3rs3}
```
## Bosqich 3 (Muqobil): Native Library Reverse Engineering

Agar 2-bosqichda emulatorda ishlatish imkoni bo'lmasa, flagni to'g'ridan-to'g'ri `.so` fayldan olish mumkin. Bu eng qiyin yo'l.

### 3.1 Native library ni chiqarish

```bash
# APK ni unzip qilish
unzip CryptoMessenger.apk -d extracted/

# .so faylni topish
ls extracted/lib/x86_64/
# → libmsgcore.so
```

### 3.2 Ghidra da ochish

`libmsgcore.so` ni **Ghidra** yoki **IDA Pro** da ochamiz va `Java_com_ctf_cryptomessenger_SecretChatActivity_b` funksiyasini topamiz.

Bu funksiya quyidagilarni bajaradi:
1. `_st` o'zgaruvchisi 1 ekanligini tekshiradi (state gate)
2. `/proc/self/status` dan `TracerPid` ni o'qiydi (anti-debug)
3. 10 ta segment (`_d0` — `_d9`) ni 2 ta XOR key (`_x0`, `_x1`) bilan decrypt qiladi
4. Natijani `jbyteArray` sifatida qaytaradi

### 3.3 XOR kalitlarini topish

Ghidra da `.rodata` seksiyasidan quyidagi ma'lumotlarni topamiz:

```
_x0 = [0x9a, 0x3c, 0x71, 0xf2, 0x58, 0xe1, 0x0b, 0xd7]  (8 bytes)
_x1 = [0xab, 0x0f, 0x42, 0xc1, 0x6b, 0xd2, 0x38, 0xe4]  (8 bytes)
```

Shifrlangan segmentlar:
```
_d0 = [0xd9, 0x74, 0x32, 0x89]  →  XOR _x0[0:4]
_d1 = [0x3c, 0xd2, 0x38, 0xa7]  →  XOR _x0[4:8]
_d2 = [0xf4, 0x63, 0x73, 0xaf]  →  XOR _x1[0:4]
...va hokazo
```

### 3.4 Decrypt script yozish

```python
x0 = [0x9a, 0x3c, 0x71, 0xf2, 0x58, 0xe1, 0x0b, 0xd7]
x1 = [0xab, 0x0f, 0x42, 0xc1, 0x6b, 0xd2, 0x38, 0xe4]

segments = [
    ([0xd9, 0x74, 0x32, 0x89], x0, 0),
    ([0x3c, 0xd2, 0x38, 0xa7], x0, 4),
    ([0xf4, 0x63, 0x73, 0xaf], x1, 0),
    ([0x00, 0x8d, 0x5b, 0x8c], x1, 4),
    ([0xae, 0x0d, 0x1f, 0xad], x0, 0),
    ([0x2c, 0xd1, 0x54, 0xb9], x0, 4),
    ([0x9f, 0x7b, 0x73, 0xb7], x1, 0),
    ([0x58, 0x8d, 0x4a, 0xd7], x1, 4),
    ([0xec, 0x0f, 0x03, 0x81], x0, 0),
    ([0x6b, 0x9c],             x0, 4),
]

flag = ""
for data, key, offset in segments:
    for i, b in enumerate(data):
        flag += chr(b ^ key[offset + i])

print(flag)
```

## Flag

`CHC{...}`
