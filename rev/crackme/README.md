# CrackMe

| Field | Value |
|-------|-------|
| Category | Rev |
| Points | ? |

## Description

> Reverse engineer the stripped 64-bit binary and find the correct password.
>
> `./crackme`

## Solution

# CrackMe — Reverse Engineering Writeup

**Kategoriya:** Reverse Engineering  
**Qiyinlik:** Medium  
**Flag formati:** `CHC{...}`  

## 1-Qadam: Dastlabki tahlil (Reconnaissance)

Avval faylning turini aniqlaymiz:

```bash
$ file crackme
crackme: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), 
dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, 
for GNU/Linux 3.2.0, stripped
```

**Nimani bildik:**
- Bu **64-bitli Linux ELF** fayl
- **Dynamically linked** — tizim kutubxonalaridan foydalanadi
- **Stripped** — barcha debug symbollar o'chirilgan, funksiya nomlari yo'q

Endi `strings` buyrug'i bilan ichidagi matnlarni ko'ramiz:

```bash
$ strings crackme | head -20
```

**Natija:** `"Enter the flag: "` va `"CHC{"` topiladi, lekin `"Correct"` yoki `"Wrong"` kabi xabarlar **topilmaydi**. Bu shuni anglatadiki, muvaffaqiyat/xato xabarlari qandaydir tarzda **obfuscate** qilingan (yashirilgan).

Dasturni ishga tushirib ko'ramiz:

```bash
$ ./crackme
Enter the flag: CHC{test}
Wrong flag! Try again.

$ ./crackme
Enter the flag: hello
Wrong flag! Try again.
```

Demak, dastur flagni kiritishni so'raydi va tekshiradi. Flag formati `CHC{...}` ekanini `strings` natijasidan ham ko'rib turibmiz.

---

## 2-Qadam: Anti-Debug tekshiruvi

Dasturni GDB bilan debug qilib ko'ramiz:

```bash
$ gdb ./crackme
(gdb) run
Starting program: /home/kali/ctf/crackme/crackme
Error: initialization failed
[Inferior 1 (process 12345) exited with code 01]
```

**GDB bilan ishga tushirganda dastur "initialization failed" deb chiqib ketdi!** Bu klassik **anti-debug** texnikasi.

### Sababi: `ptrace` tekshiruvi

Ghidra da ko'rsak, dastur boshida `ptrace(PTRACE_TRACEME, ...)` chaqiradi. Bu nima qiladi:
- Agar dastur **oddiy** ishga tushsa — `ptrace` muvaffaqiyatli bo'ladi (0 qaytaradi)
- Agar dastur **debugger ostida** ishga tushsa — `ptrace` **-1 qaytaradi** (chunki debugger allaqachon trace qilmoqda)

Natijada dastur debugger borligini aniqlaydi va o'zini to'xtatadi.

### Bypass usullari:

**1-usul: Ghidra/IDA da patching**
Ptrace tekshiruvini `NOP` bilan almashtiramiz yoki `jne` ni `je` ga o'zgartiramiz.

**2-usul: LD_PRELOAD**
Soxta `ptrace` funksiyasi yozamiz:

```c
// bypass_ptrace.c
long ptrace(int request, ...) { return 0; }
```

```bash
$ gcc -shared -o bypass.so bypass_ptrace.c
$ LD_PRELOAD=./bypass.so gdb ./crackme
```

**3-usul: GDB da catch**
```
(gdb) catch syscall ptrace
(gdb) run
(gdb) # ptrace chaqirilganda to'xtaydi, rax ni 0 ga o'zgartiramiz
(gdb) set $rax = 0
(gdb) continue
```

Lekin biz asosan **statik tahlil** (Ghidra) dan foydalanamiz, shuning uchun anti-debug katta muammo emas.

---

## 3-Qadam: Ghidra bilan statik tahlil

### 3.1 — Main funksiyasini topish

Binaryni Ghidra da ochamiz. `stripped` bo'lgani uchun funksiya nomlari yo'q, lekin `entry` nuqtasidan `__libc_start_main` ga o'tib, birinchi argument sifatida berilgan manzilni `main` deb belgilaymiz.

### 3.2 — Main ning tuzilishi

Ghidra decompiler ko'rsatadigan kod taxminan shunday:

```c
// Soddalashtirilgan pseudocode
int main() {
    // 1. Anti-debug: ptrace tekshiruvi
    if (ptrace(PTRACE_TRACEME, 0, 0, 0) == -1) {
        fprintf(stderr, "Error: initialization failed\n");
        return 1;
    }

    // 2. Input o'qish
    printf("Enter the flag: ");
    fgets(input, 128, stdin);
    
    // 3. "CHC{" va "}" tekshiruvi
    if (strncmp(input, "CHC{", 4) != 0 || input[len-1] != '}')
        goto fail;
    
    // 4. Ichki qismni ajratib, verify_inner() ga berish
    if (verify_inner(inner, inner_len))
        print_obfuscated(win_msg);   // Muvaffaqiyat!
    else
        print_obfuscated(fail_msg);  // Xato!
}
```

### 3.3 — Chalg'ituvchi (decoy) funksiyalar

Binaryda ikkita **chalg'ituvchi funksiya** bor — ular **hech qachon chaqirilmaydi**, faqat reverserni chalg'itish uchun:

| Funksiya | Nima qiladi | Haqiqiymi? |
|---|---|---|
| `fake_check()` | Har bir belgini indeksga ko'paytirib yig'adi, 7331 bilan solishtiradi | Soxta |
| `decoy_transform()` | ROT13 ga o'xshash transform qiladi | Soxta |

**Muhim:** Bu funksiyalarga reference (`CALL`, `XREF`) **yo'q**. `main()` dan faqat `verify_inner()` chaqiriladi — shu haqiqiy tekshiruv funksiyasi.

### 3.4 — Obfuscated stringlar

`print_obfuscated()` funksiyasi har bir baytni `0x5A` bilan XOR qilib chiqaradi:

```c
void print_obfuscated(uint8_t *data) {
    while (*data != 0) {
        putchar(*data ^ 0x5A);
        data++;
    }
}
```

Bu sababli `"Correct!"` va `"Wrong!"` xabarlari `strings` da ko'rinmaydi — ular XOR qilingan holda saqlangan.

---

## 4-Qadam: Asosiy tahlil — `verify_inner()` funksiyasi

Bu eng muhim qism! Funksiya flagning ichki qismini (ya'ni `CHC{` va `}` orasidagi matn) oladi va **3 bosqichli transformatsiya** qiladi:

### Stage 1: XOR shifrlash

```c
void stage1_xor(uint8_t *data, size_t len) {
    uint8_t key[] = { 0x13, 0x37, 0x42, 0xBE, 0xEF };
    for (int i = 0; i < len; i++) {
        data[i] ^= key[i % 5];
    }
}
```

Har bir bayt 5-elementli kalit bilan **XOR** qilinadi. Kalit **aylanma** — 5 baytdan keyin qayta boshlanadi.

### Stage 2: Shuffle (aralashtirish)

```c
void stage2_shuffle(uint8_t *data, size_t len) {
    // 1. Juft-toq juftliklarni almashtiramiz
    for (int i = 0; i + 1 < len; i += 2) {
        swap(data[i], data[i+1]);
    }
    // 2. Har bir baytga (indeks * 3) qo'shamiz
    for (int i = 0; i < len; i++) {
        data[i] = (data[i] + i * 3) & 0xFF;
    }
}
```

Bu bosqichda **ikki narsa** bo'ladi:
1. Qo'shni baytlar juftligi almashtiriladi: `[A,B,C,D]` → `[B,A,D,C]`
2. Har bir baytga `indeks × 3` qo'shiladi

### Stage 3: Bit aylantirish (bit rotation)

```c
void stage3_bitrot(uint8_t *data, size_t len) {
    for (int i = 0; i < len; i++) {
        data[i] = (data[i] << 3) | (data[i] >> 5);
    }
}
```

Har bir bayt **3 bit chapga aylantiriladi** (rotate left). Bu oddiy shift emas — tushib ketgan bitlar o'ng tomonga qaytadi.

### Solishtirish

3 ta stage dan keyin natija quyidagi **hardcoded massiv** bilan solishtiriladi:

```c
static const uint8_t target[] = {
    0x38, 0x73, 0x3f, 0xc9, 0x3c, 0x5d, 0xb1, 0xd8,
    0x46, 0x2f, 0x34, 0xf4, 0x6f, 0xc2, 0x6c, 0x40,
    0x32
};
```

Solishtirish **timing-safe** usulda amalga oshiriladi (XOR natijalarini OR qilib, oxirida 0 ekanini tekshiradi). Bu side-channel hujumdan himoya qiladi.

Ichki qism uzunligi aynan **17 bayt** bo'lishi kerak — aks holda darhol rad etiladi.

---

## 5-Qadam: Algoritmni teskari yozish (Reverse the algorithm)

Endi biz algoritmni **teskari tartibda** qo'llaymiz. Ya'ni: `stage3` → `stage2` → `stage1` tartibida, har birining **inversiyasini** yozamiz.

### Teskari Stage 3: Bit aylantirish — o'ngga

```python
def reverse_stage3(data):
    """Chapga 3 bit aylantirishning teskarisi = o'ngga 3 bit"""
    result = []
    for b in data:
        result.append(((b >> 3) | (b << 5)) & 0xFF)
    return result
```

### Teskari Stage 2: Shuffle — teskari tartibda

```python
def reverse_stage2(data):
    """Avval indeks qo'shishni qaytaramiz, keyin juftliklarni almashtramiz"""
    result = list(data)
    # 1. (i * 3) ni ayiramiz
    for i in range(len(result)):
        result[i] = (result[i] - (i * 3)) & 0xFF
    # 2. Juftliklarni qayta almashtiramiz (swap o'ziga teskari)
    for i in range(0, len(result) - 1, 2):
        result[i], result[i + 1] = result[i + 1], result[i]
    return result
```

### Teskari Stage 1: XOR — xuddi shu kalit bilan

```python
def reverse_stage1(data):
    """XOR o'ziga teskari: A ^ K ^ K = A"""
    key = [0x13, 0x37, 0x42, 0xBE, 0xEF]
    result = []
    for i, b in enumerate(data):
        result.append(b ^ key[i % len(key)])
    return result
```

> [!TIP]
> XOR operatsiyasi **o'ziga teskari** (self-inverse) — ya'ni bir xil kalit bilan ikki marta XOR qilsangiz, asl qiymat qaytadi. Shuning uchun stage 1 ning inversiyasi xuddi o'zi.

---

## 6-Qadam: Solver skriptni ishga tushirish

Hammasini birlashtiramiz:

```python
#!/usr/bin/env python3

def reverse_stage3(data):
    return [((b >> 3) | (b << 5)) & 0xFF for b in data]

def reverse_stage2(data):
    result = list(data)
    for i in range(len(result)):
        result[i] = (result[i] - (i * 3)) & 0xFF
    for i in range(0, len(result) - 1, 2):
        result[i], result[i + 1] = result[i + 1], result[i]
    return result

def reverse_stage1(data):
    key = [0x13, 0x37, 0x42, 0xBE, 0xEF]
    return [b ^ key[i % len(key)] for i, b in enumerate(data)]

# Binarydan olingan target massiv
target = [
    0x38, 0x73, 0x3f, 0xc9, 0x3c, 0x5d, 0xb1, 0xd8,
    0x46, 0x2f, 0x34, 0xf4, 0x6f, 0xc2, 0x6c, 0x40,
    0x32
]

# Teskari tartibda qo'llaymiz: stage3 → stage2 → stage1
step1 = reverse_stage3(target)
step2 = reverse_stage2(step1)
step3 = reverse_stage1(step2)

inner = ''.join(chr(b) for b in step3)
flag = f"CHC{{{inner}}}"
print(f"[+] Flag: {flag}")
```

```bash
$ python3 solve.py
[+] Flag: CHC{x0r_sh1ft_n_sw4p!}
```

---

## 7-Qadam: Tasdiqlash

```bash
$ echo 'CHC{x0r_sh1ft_n_sw4p!}' | ./crackme
Enter the flag: Correct! You got the flag!
```


## Flag

`CHC{x0r_sh1ft_n_sw4p!}`
