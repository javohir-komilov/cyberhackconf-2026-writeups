# CTF MISC — Yozish (Server tomonida, Ctrl+U oqish yo'q)

> **Maqsad:** Parolni to'plash, administrator sifatida tizimga kirish, /flag ni ochish.

> Ushbu CTF da parol va bayroq HTML/JS da yo'q, shuning uchun Ctrl+U ishlamaydi.

---

## Qisqacha: Yechim zanjiri

`/robots.txt` → (yoki `/hints/*`) → `/api/ping` (**X-CTF** sarlavhasi)
→ **base64 ni dekodlash → hex → rot13** → yo'l `/internal/door`
→ **PREFIX_B64** ni olish → **k1** va **k2** ni olish → parolni yig'ish
→ `/login?u=admin` → `/flag` `

---

## 1-qadam — robots.txt

Ochish:

- `http://localhost:8000/robots.txt`

*CTF maslahatlari* (`Ruxsat bermaslik: /hints/`) ataylab u yerda qoldiriladi.
Fikr: **“Ruxsat bermaslik” ko'pincha qiziqarli yo'llarga ishora qiladi**.

---

## 2-qadam — hints/assets

Quyidagi manzilga o'ting:

- `http://localhost:8000/hints/step1.txt`, `http://localhost:8000/hints/step2.txt`

Keyingi qadam oxirgi nuqta bilan bog'liqligi haqida ishora bo'ladi:

- `/api/ping`

---

## 3-qadam — /api/ping va X-CTF sarlavhasi

Oxirgi nuqtani so'rang va javob sarlavhalariga qarang:

```bash
curl -i http://localhost:8000/api/ping
```

Qatorni toping:

```
X-Ctf: <VALUE>
```

`<VALUE>` **3 qatlamda** kodlangan satr:

1) base64
2) hex
3) rot13

Ushbu uchta bosqichdan so'ng, keyingi qadam uchun yo'lni (URL) olasiz.

---

## 4-qadam — Dekodlash: base64 → hex → rot13

### Bir qatorli (Linux/Kali/WSL)

`X-Ctf` dan qiymatni almashtiring:

```bash
echo 'PASTE_X_CTF_HERE' | base64 -d | xxd -r -p | tr 'A-Za-z' 'N-ZA-Mn-za-m'
```

Kutilayotgan natija:

```
/internal/door
```

### Bosqichma-bosqich (agar kerak bo'lsa)

**4.1** base64 dekodlash:

```bash
echo 'PASTE_X_CTF_HERE' | base64 -d
```

siz hex qatorini olasiz.

**4.2** hex dekodlash:

```bash
echo 'HEX_FROM_PREVIOUS_STEP' | xxd -r -p
```

rot13 da satrni olasiz.

**4.3** rot13 dekodlash:

```bash
echo 'ROT13_STRING' | tr 'A-Za-z' 'N-ZA-Mn-za-m'
```

yo'lni olasiz.

---

## 5-qadam — /internal/door va PREFIX_B64

Ochish:

- `http://localhost:8000/internal/door`

U yerda siz quyidagilarni ko'rasiz:

- `PREFIX_B64=...`

Dekode qilish:

```bash
echo 'PREFIX_B64_VALUE' | base64 -d
```

Kutilgan parol prefiksi chiqariladi, masalan:

```
admin_@#$_
```

---

## 6-qadam — asosiy qismlar: /internal/k1 va /internal/k2

### 6.1 Key1 (base64 → reverse)

```bash
curl -s http://localhost:8000/internal/k1 | cut -d= -f2 | head -n1 | base64 -d | rev
```

Chiqish prefiksdan keyingi birinchi qism bo'ladi, masalan:

```
098123
```

### 6.2 Key2 (hex-bytes → ASCII)

```bash
curl -s http://localhost:8000/internal/k2 | cut -d= -f2 | head -n1 | xxd -r -p
```

Chiqish natijasi ikkinchi qism bo'ladi, masalan:

```
4765
```

---

## 7-qadam — Parol yaratish

Formula:

```
FINAL_PASSWORD = prefiks + 1-qism + 2-qism
```

Misol:

```
admin_@#$_ + 098123 + 4765
= admin_@#$_0981234765
```

---

## 8-qadam — Kirish va bayroqcha qo'yish

Ochish:

- `http://localhost:8000/login?u=admin`

Kirish:

- **foydalanuvchi nomi:** `admin`
- **password:** `FINAL_PASSWORD`

Kirgandan so'ng, oching:

- `http://localhost:8000/flag`

---

## Keyin yakunlash

- `http://localhost:8000/writeup` — tahlil sahifasi (kirishdan keyin kirish mumkin)

---

## Nima uchun Ctrl+U yordam bermaydi

- parol va bayroq HTML/JS da **emas**;
- tekshirish serverda** amalga oshiriladi (O'tish);
- maslahatlar quyidagilarga taqsimlangan: `robots.txt`, `assets/hints` dagi fayllar, javob sarlavhalari va "ichki" oxirgi nuqtalar.

---

## Buyruq cheat varag'i (hamma narsa tez)

```bash
# 1) X-CTF ni olish
curl -i http://localhost:8000/api/ping

# 2) yo'lga dekodlash
echo 'PASTE_X_CTF_HERE' | base64 -d | xxd -r -p | tr 'A-Za-z' 'N-ZA-Mn-za-m'

#3) prefiks
# (/internal/door dan PREFIX_B64 o'rniga qo'ying)
echo 'PASTE_PREFIX_B64_HERE' | base64 -d

#4) k1 + k2
curl -s http://localhost:8000/internal/k1 | cut -d= -f2 | head -n1 | base64 -d | rev
curl -s http://localhost:8000/internal/k2 | cut -d= -f2 | head -n1 | xxd -r -p
```