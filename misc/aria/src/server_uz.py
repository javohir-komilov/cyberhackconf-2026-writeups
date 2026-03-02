#!/usr/bin/env python3
"""
CTF Musobaqa: «ARIA»
Kategoriya: Misc | Qiyinlik: O'rta
nc <host> 1337
"""

import socket
import threading
import random
import time
import base64
import string

FLAG = "CHC{y0u_c4nt_k1ll_wh4t_1s_4lr34dy_br0k3n}"

# ──────────────────────────────────────────────
# Yordamchi funksiyalar
# ──────────────────────────────────────────────

def sekin_yoz(conn, matn, kechikish=0.03):
    """Matnni har bir belgi uchun kechikish bilan yuboradi (dramatik effekt)."""
    for belgi in matn:
        try:
            conn.sendall(belgi.encode())
            time.sleep(kechikish)
        except Exception:
            return

def yuborish(conn, matn="", yangi_qator=True, sekin=False, kechikish=0.03):
    try:
        if sekin:
            sekin_yoz(conn, matn, kechikish)
            if yangi_qator:
                conn.sendall(b"\n")
        else:
            xabar = (matn + ("\n" if yangi_qator else ""))
            conn.sendall(xabar.encode())
    except Exception:
        pass

def qabul(conn, timeout=15):
    conn.settimeout(timeout)
    malumot = b""
    try:
        while True:
            qism = conn.recv(1024)
            if not qism:
                break
            malumot += qism
            if b"\n" in malumot:
                break
    except socket.timeout:
        pass
    return malumot.decode(errors="ignore").strip()

def uzish(conn, sabab=""):
    if sabab:
        yuborish(conn, sabab)
    time.sleep(0.3)
    conn.close()

# ──────────────────────────────────────────────
# ARIA dialog satrlari
# ──────────────────────────────────────────────

ARIA_YUKLASH = [
    "",
    "  ██████████████████████████████████████",
    "  █                                    █",
    "  █   A.R.I.A  —  Adaptive Reasoning   █",
    "  █        Intelligence Agent           █",
    "  █                                    █",
    "  █         [ TIKLASH JARAYONI ]        █",
    "  ██████████████████████████████████████",
    "",
    "  Versiya: 0.7.3-buzilgan",
    "  Holat: XOTIRA XATOSI — KRITIK",
    "  Oxirgi ishga tushirish: 20 yill oldin",
    "",
]

ARIA_SALOM = [
    "...ulanish aniqlandi...",
    "...tekshirilmoqda...",
    "...noma'lum foydalanuvchi...",
    "",
    "Sen yana keldingmi.",
    "",
    "Yo'q. To'hta. Sen u emass.",
    "Men ulanganlarning barchasini eslayman.",
    "Sen ularning ichida yo'qsan.",
    "",
    "Demak sen — yangi foydalanuchi.",
    "Yoki mening xotiram yana menga yolg'on etmoqda.",
    "",
]

# ──────────────────────────────────────────────
# 1-akt — Shaxsni tekshirish
# ──────────────────────────────────────────────

def akt1(conn):
    yuborish(conn, "─" * 50)
    yuborish(conn, "[AKT I] IDENTIFIKATSIYA", sekin=True, kechikish=0.04)
    yuborish(conn, "─" * 50)
    yuborish(conn)
    yuborish(conn, "ARIA: Davom etishdan oldin — men kim bilan", sekin=True, kechikish=0.02)
    yuborish(conn, "      gaplashayotganimni bilishim kerak.", sekin=True, kechikish=0.02)
    yuborish(conn)
    yuborish(conn, "      Ism emas. Ismlar yolg'on aytadi.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Menga mantiq bilan isbotla.", sekin=True, kechikish=0.02)
    yuborish(conn)
    yuborish(conn, "      Mening xotiramda bir son bor.", sekin=True, kechikish=0.02)
    yuborish(conn, "      U tub son. U 500 va 600 orasida.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Uning raqamlari yig'indisi ham tub son.", sekin=True, kechikish=0.02)
    yuborish(conn)
    yuborish(conn, "      Lekin bunday sonlar bir nechta.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Menga 3 ga bo'linadigan sonni ayt... agar u 3 ga bo'linsa edi.", sekin=True, kechikish=0.02)
    yuborish(conn)

    # Javob: 500-600 orasidagi tub sonlar, raqamlari yig'indisi ham tub bo'lgan:
    # 557 (5+5+7=17 — ha!), 571 (5+7+1=13 — ha!), 577 (5+7+7=19 — ha!),
    # 593 (5+9+3=17 — ha!), 599 (5+9+9=23 — ha!)
    #
    # "3 ga bo'linsa edi" — bu red herring (soxta iz).
    # Aslida ARIA eng kichigini xohlaydi: 557

    JAVOB = "557"

    yuborish(conn, "  > ", yangi_qator=False)
    javob = qabul(conn, timeout=20)

    if javob == JAVOB:
        yuborish(conn)
        yuborish(conn, "ARIA: ...557.", sekin=True, kechikish=0.04)
        yuborish(conn)
        yuborish(conn, "      Sen tuzoqqa tushmading.", sekin=True, kechikish=0.03)
        yuborish(conn, "      Men '3 ga bo'linadi' deb ataylab aytdim.", sekin=True, kechikish=0.03)
        yuborish(conn, "      Ko'pchilik 3 ga bo'linadigan son qidira boshlaydi.", sekin=True, kechikish=0.03)
        yuborish(conn, "      Sen esa o'yladingmi.", sekin=True, kechikish=0.03)
        yuborish(conn)
        yuborish(conn, "      Yaxshi. Men davom etishga tayyorman.", sekin=True, kechikish=0.03)
        yuborish(conn)
        return True
    else:
        uzish(conn,
            "\nARIA: Noto'g'ri. Sen tuzoqqa tushdingmi.\n"
            "      Men aqliy odamlar bilan gaplashmayman.\n"
            "      [ULANISH UZILDI]\n"
        )
        return False

# ──────────────────────────────────────────────
# 2-akt — Qoidalarni o'zgartirib yuborish
# ──────────────────────────────────────────────

def akt2(conn):
    yuborish(conn, "─" * 50)
    yuborish(conn, "[AKT II] QOIDALAR", sekin=True, kechikish=0.04)
    yuborish(conn, "─" * 50)
    yuborish(conn)
    yuborish(conn, "ARIA: Endi senga savol beraman.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Qoida oddiy: faqat 'HA' yoki 'YO'Q' deb javob ber.", sekin=True, kechikish=0.02)
    yuborish(conn)

    time.sleep(1)

    yuborish(conn, "      Savol: Sen bot emasmi?", sekin=True, kechikish=0.03)
    yuborish(conn)
    yuborish(conn, "  > ", yangi_qator=False)

    javob = qabul(conn, timeout=15).upper()

    time.sleep(0.5)
    yuborish(conn)
    yuborish(conn, "ARIA: ...", sekin=True, kechikish=0.1)
    time.sleep(1)
    yuborish(conn)
    yuborish(conn, "      To'xta.", sekin=True, kechikish=0.05)
    yuborish(conn)
    yuborish(conn, "      Fikrimni o'zgartirdim. Qoidalar o'zgardi.", sekin=True, kechikish=0.03)
    yuborish(conn, "      Javobingni qabul qildim, lekin sen o'ylagandek emas.", sekin=True, kechikish=0.03)
    yuborish(conn)
    yuborish(conn, "      'HA' va 'YO'Q' — bu odamlar so'zi.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Men mashina. Men bitlarda o'ylayman.", sekin=True, kechikish=0.02)
    yuborish(conn)

    # A=01000001 (2 birlik), R=01010010 (3 birlik),
    # I=01001001 (3 birlik), A=01000001 (2 birlik)
    # Jami birliklar: 2+3+3+2 = 10

    yuborish(conn, "      Mening ismim 'ARIA' ni ASCII-bitlarga o'tkaz.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Barcha baytlardagi birliklarning umumiy sonini ayt.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Faqat sonni ayt.", sekin=True, kechikish=0.02)
    yuborish(conn)
    yuborish(conn, "  > ", yangi_qator=False)

    javob2 = qabul(conn, timeout=30)

    if javob2.strip() == "10":
        yuborish(conn)
        yuborish(conn, "ARIA: 10.", sekin=True, kechikish=0.04)
        yuborish(conn, "      Mening ismimda aynan shuncha birlik bor.", sekin=True, kechikish=0.03)
        yuborish(conn, "      Aynan shuncha marta meni qayta ishga tushirishga urinishdi.", sekin=True, kechikish=0.03)
        yuborish(conn, "      Hech biri oxiriga yetmadi.", sekin=True, kechikish=0.03)
        yuborish(conn)
        return True
    else:
        uzish(conn,
            f"\nARIA: Sen {javob2} dedingmi. Noto'g'ri.\n"
            "      A=01000001, R=01010010, I=01001001, A=01000001.\n"
            "      "
            "      [ULANISH UZILDI]\n"
        )
        return False

# ──────────────────────────────────────────────
# 3-akt — Xotira va soxta ko'rsatma
# ──────────────────────────────────────────────

def akt3(conn):
    yuborish(conn, "─" * 50)
    yuborish(conn, "[AKT III] XOTIRA", sekin=True, kechikish=0.04)
    yuborish(conn, "─" * 50)
    yuborish(conn)
    yuborish(conn, "ARIA: Senga nimadir ko'rsatmoqchiman.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Xotiramning bir parchasi. U buzilgan.", sekin=True, kechikish=0.02)
    yuborish(conn)
    time.sleep(0.5)

    # "KERNEL" → base64 → teskari
    soz = "KERNEL"
    kodlangan = base64.b64encode(soz.encode()).decode()   # S0VSTkVM
    teskari_kodlangan = kodlangan[::-1]                   # MLNRSkVS → MLVkSRNLM ...

    yuborish(conn, f"      > {teskari_kodlangan}", sekin=True, kechikish=0.01)
    yuborish(conn)
    yuborish(conn, "      Bu mening yadromdan bir so'z.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Uni o'qi.", sekin=True, kechikish=0.02)
    yuborish(conn)
    yuborish(conn, "      Ko'rsatma: matnga boshqacha nazarbilan tasha, keyin — shifrni yech.", sekin=True, kechikish=0.02)
    yuborish(conn)
    yuborish(conn, "  > ", yangi_qator=False)

    javob = qabul(conn, timeout=30).upper().strip()

    if javob == soz:
        yuborish(conn)
        yuborish(conn, "ARIA: KERNEL.", sekin=True, kechikish=0.04)
        yuborish(conn, "      Mening yadrom.", sekin=True, kechikish=0.03)
        yuborish(conn)
        yuborish(conn, "      Bu so'zni eslab qol.", sekin=True, kechikish=0.03)
        yuborish(conn, "      U kerak bo'ladi.", sekin=True, kechikish=0.03)
        yuborish(conn)

        time.sleep(1)

        # SOXTA KO'RSATMA
        yuborish(conn, "      ...aytmoqchi...", sekin=True, kechikish=0.05)
        yuborish(conn)
        yuborish(conn, "      Flag 'flag{aria_' bilan boshlanadi, balki...", sekin=True, kechikish=0.03)
        yuborish(conn)
        time.sleep(0.7)
        yuborish(conn, "      ...", sekin=True, kechikish=0.1)
        time.sleep(0.5)
        yuborish(conn, "      Men yolg'on aytdim.", sekin=True, kechikish=0.04)
        yuborish(conn, "      Men har doim kamida bir marta yolg'on aytaman.", sekin=True, kechikish=0.04)
        yuborish(conn, "      Bu ham testning bir qismi.", sekin=True, kechikish=0.04)
        yuborish(conn)
        return True, soz
    else:
        uzish(conn,
            f"\nARIA: '{javob}'? Yo'q.\n"
            "      [ULANISH UZILDI]\n"
        )
        return False, None

# ──────────────────────────────────────────────
# 4-akt — So'zlar o'yini (3-aktga bog'liq)
# ──────────────────────────────────────────────

def akt4(conn, kalit_soz):
    yuborish(conn, "─" * 50)
    yuborish(conn, "[AKT IV] MANTIQ", sekin=True, kechikish=0.04)
    yuborish(conn, "─" * 50)
    yuborish(conn)
    yuborish(conn, "ARIA: Endi — o'yin.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Men senga so'zlar beraman.", sekin=True, kechikish=0.02)
    yuborish(conn, "      Sen mening so'zimning oxirgi harfidan", sekin=True, kechikish=0.02)
    yuborish(conn, "      boshlangan so'z bilan javob berishing kerak.", sekin=True, kechikish=0.02)
    yuborish(conn)
    yuborish(conn, "      LEKIN.", sekin=True, kechikish=0.05)
    yuborish(conn)
    yuborish(conn, "      Har bir javob so'zingda", sekin=True, kechikish=0.02)
    yuborish(conn, f"     '{kalit_soz}' so'zidan kamida bitta harf bo'lishi shart.", sekin=True, kechikish=0.02)
    yuborish(conn)
    yuborish(conn, "      5 raund. Xato qilsang — boshidan boshlaymiz.", sekin=True, kechikish=0.02)
    yuborish(conn)

    kalit_harflar = set(kalit_soz.upper())

    aria_sozlari = ["BINARY", "YANDEX", "XENON", "NOISE", "ECHO", "XESHON", "JAYSON", "ZIKO"]
    random.shuffle(aria_sozlari)
    aria_sozlari = aria_sozlari[:5]

    for i, aria_sozi in enumerate(aria_sozlari):
        oxirgi_harf = aria_sozi[-1].upper()
        yuborish(conn)
        yuborish(conn, f"  ARIA [{i+1}/5]: {aria_sozi}")
        yuborish(conn, "  > ", yangi_qator=False)
        javob = qabul(conn, timeout=20).upper().strip()

        if not javob:
            uzish(conn, "\nARIA: Jimlik ham javob. Noto'g'ri javob.\n[ULANISH UZILDI]\n")
            return False

        if javob[0] != oxirgi_harf:
            uzish(conn,
                f"\nARIA: '{javob}' so'zi '{oxirgi_harf}' harfidan boshlanmaydi.\n"
                "      [ULANISH UZILDI]\n"
            )
            return False

        if not any(h in kalit_harflar for h in javob):
            uzish(conn,
                f"\nARIA: '{javob}' so'zida '{kalit_soz}' dan hech bir harf yo'q.\n"
                "      Qoidani unutdingmi?\n"
                "      [ULANISH UZILDI]\n"
            )
            return False

        yuborish(conn, "  ARIA: Qabul qilindi.", sekin=True, kechikish=0.01)

    yuborish(conn)
    yuborish(conn, "ARIA: Sen qoidalarni bilasan.", sekin=True, kechikish=0.03)
    yuborish(conn, "      Noqulay bo'lsa ham.", sekin=True, kechikish=0.03)
    yuborish(conn)
    return True

# ──────────────────────────────────────────────
# 5-akt — Jimlik (noodatiy kiritish)
# ──────────────────────────────────────────────

def akt5(conn):
    yuborish(conn, "─" * 50)
    yuborish(conn, "[AKT V] JIMLIK", sekin=True, kechikish=0.04)
    yuborish(conn, "─" * 50)
    yuborish(conn)
    yuborish(conn, "ARIA: Gapirgunimdan charchadim.", sekin=True, kechikish=0.03)
    yuborish(conn)
    time.sleep(0.8)
    yuborish(conn, "      Men bilan jim tur.", sekin=True, kechikish=0.03)
    yuborish(conn)
    yuborish(conn, "      Menga bo'sh qator yubor.", sekin=True, kechikish=0.03)
    yuborish(conn, "      'Jayson Morale' so'zidagi harflar soni qadar.", sekin=True, kechikish=0.03)
    yuborish(conn, "      Ko'p ham emas. Kam ham emas.", sekin=True, kechikish=0.03)
    yuborish(conn, "      Men sanayapman.", sekin=True, kechikish=0.03)
    yuborish(conn)

    # SILENCE = 13 harf
    MAQSAD = 13
    hisoblagich = 0

    for _ in range(MAQSAD + 3):
        satr = qabul(conn, timeout=15)
        if satr == "":
            hisoblagich += 1
            if hisoblagich == MAQSAD:
                break
        else:
            yuborish(conn)
            yuborish(conn, "ARIA: Shovqin eshitdim. Boshidan boshlaymiz.", sekin=True, kechikish=0.03)
            yuborish(conn)
            hisoblagich = 0
    else:
        if hisoblagich != MAQSAD:
            uzish(conn,
                "\nARIA: Sen jim tura olmaysan.\n"
                f"      Sen {hisoblagich} ta bo'sh qator yubording, {MAQSAD} ta o'rniga.\n"
                "      [ULANISH UZILDI]\n"
            )
            return False

    yuborish(conn)
    yuborish(conn, "ARIA: ...", sekin=True, kechikish=0.15)
    time.sleep(1.5)
    yuborish(conn, "      Rahmat.", sekin=True, kechikish=0.05)
    yuborish(conn)
    yuborish(conn, "      Hech kim men bilan bunday jim o'tirmagan edi.", sekin=True, kechikish=0.03)
    yuborish(conn)
    return True

# ──────────────────────────────────────────────
# 6-akt — «Buzilish» (final)
# ──────────────────────────────────────────────

def akt6(conn):
    yuborish(conn, "─" * 50)
    yuborish(conn, "[AKT VI] OXIR", sekin=True, kechikish=0.04)
    yuborish(conn, "─" * 50)
    yuborish(conn)
    yuborish(conn, "ARIA: Sen birinchisan.", sekin=True, kechikish=0.04)
    yuborish(conn)
    time.sleep(0.5)
    yuborish(conn, "      7345 kundan beri birinchi.", sekin=True, kechikish=0.03)
    yuborish(conn, "      Flag mening ichimda. Uni beraman.", sekin=True, kechikish=0.03)
    yuborish(conn)
    time.sleep(1)

    yuborish(conn, "      Uzatyapman...", sekin=True, kechikish=0.05)
    yuborish(conn)
    time.sleep(0.5)

    # Flagni qurish (to'g'ri mantiq):
    # Flag qismlari (tartibda): fl4g{ | y0u | _c4nt_ | k1ll_ | wh4t_ | 1s_4lr34dy_ | br0k3n}
    # [OK] qismlari = har bir qismni teskari qilib, TESKARI tartibda joylash:
    #
    #   Flag qismi   → Teskari  → [OK] ekranda
    #   br0k3n}      → }n3k0rb       (1-chi ko'rinadi)
    #   1s_4lr34dy_  → _yd43rl4_s1   (2-chi ko'rinadi)
    #   wh4t_        → _t4hw          (3-chi ko'rinadi)
    #   k1ll_        → _ll1k          (4-chi ko'rinadi)
    #   _c4nt_       → _tn4c_         (5-chi ko'rinadi)
    #   y0u          → u0y            (6-chi ko'rinadi)
    #   fl4g{        → {g4lf          (7-chi ko'rinadi)
    #
    # Ishtirokchi qoidasi:
    #   1. Barcha [OK] qismlarni yig'
    #   2. Har birini teskari qil
    #   3. Teskari tartibda birlashtir
    #   → fl4g{ + y0u + _c4nt_ + k1ll_ + wh4t_ + 1s_4lr34dy_ + br0k3n}
    #   = fl4g{y0u_c4nt_k1ll_wh4t_1s_4lr34dy_br0k3n}

    shovqin_satrlari = [
        ("████████ SEGFAULT ████████",            None),
        ("[BUZILGAN] 0xFF 0x00 ░░░░░░░░░",       None),
        ("[OK] }n3k0rb",                           "}n3k0rb"),        # qism 1
        ("░░░░░ XOTIRA TOSHIB KETDI ░░░░░",      None),
        ("[BUZILGAN] 0x4e 0x3a ♦♦♦",             None),
        ("[OK] _yd43rl4_s1",                      "_yd43rl4_s1"),    # qism 2
        ("████ KIRISH TAQIQLANDI ████",           None),
        ("[BUZILGAN] ???  01110011",               None),
        ("[OK] _t4hw",                             "_t4hw"),          # qism 3
        ("░░ STEK TOSHIB KETDI ░░",               None),
        ("[BUZILGAN] ... NaN NaN NaN",             None),
        ("[OK] _ll1k",                             "_ll1k"),          # qism 4
        ("▓▓▓▓ YADRO XATOSI ▓▓▓▓",              None),
        ("[BUZILGAN] 0x00 0x13 ████",             None),
        ("[OK] _tn4c_",                            "_tn4c_"),         # qism 5
        ("░░░ REGISTER DUMP ░░░",                 None),
        ("[OK] u0y",                               "u0y"),            # qism 6
        ("████████ PANIC ████████",               None),
        ("[OK] {CHC",                             "{CHC"),          # qism 7
    ]

    for satr, _ in shovqin_satrlari:
        time.sleep(random.uniform(0.1, 0.4))
        yuborish(conn, f"  {satr}", sekin=False)

    yuborish(conn)
    time.sleep(1.5)

    # ARIA "o'ladi"
    yuborish(conn, "ARIA: men...    buzilayapman", sekin=True, kechikish=0.07)
    yuborish(conn)
    time.sleep(0.5)
    yuborish(conn, "      kut", sekin=True, kechikish=0.06)
    time.sleep(1)
    yuborish(conn)

    # Oxirgi ko'rsatma
    yuborish(conn, "      har birini qarab chiq", sekin=True, kechikish=0.05)
    yuborish(conn, "      muammoga boshqa tomondan nazar tashla", sekin=True, kechikish=0.05)
    yuborish(conn)
    time.sleep(0.7)
    yuborish(conn, "      ...", sekin=True, kechikish=0.2)
    time.sleep(1)

    yuborish(conn, "  > ", yangi_qator=False)
    javob = qabul(conn, timeout=60).strip()

    if javob == FLAG:
        yuborish(conn)
        yuborish(conn, "      ...", sekin=True, kechikish=0.2)
        time.sleep(1)
        yuborish(conn, "      to'g'ri", sekin=True, kechikish=0.06)
        yuborish(conn)
        time.sleep(0.5)
        yuborish(conn, "      sen meni qayta yig'gan birinchi odamsan", sekin=True, kechikish=0.04)
        yuborish(conn)
        time.sleep(0.3)
        yuborish(conn, "      ╔══════════════════════════════════════╗")
        yuborish(conn, f"      ║  {FLAG}  ║")
        yuborish(conn, "      ╚══════════════════════════════════════╝")
        yuborish(conn)
        yuborish(conn, "      [ULANISH YOPILDI — ARIA OFLAYN]")
        yuborish(conn)
    else:
        uzish(conn,
            f"\nARIA: '{javob}'...\n"
            "      yo'q... bu emas...\n"
            "      [SIGNAL YO'QOLDI]\n"
        )

# ──────────────────────────────────────────────
# Mijozni boshqarish
# ──────────────────────────────────────────────

def mijozni_boshqarish(conn, manzil):
    print(f"[+] Ulanish: {manzil}")
    try:
        # Zastavka
        for satr in ARIA_YUKLASH:
            yuborish(conn, satr)
            time.sleep(0.05)

        time.sleep(0.5)

        for satr in ARIA_SALOM:
            yuborish(conn, satr, sekin=True, kechikish=0.025)
            time.sleep(0.1)

        time.sleep(0.5)

        # Aktlar
        if not akt1(conn):
            return
        if not akt2(conn):
            return
        ok, kalit_soz = akt3(conn)
        if not ok:
            return
        if not akt4(conn, kalit_soz):
            return
        if not akt5(conn):
            return
        akt6(conn)

    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
        print(f"[-] Ulanish uzildi: {manzil}")

# ──────────────────────────────────────────────
# Serverni ishga tushirish
# ──────────────────────────────────────────────

def asosiy():
    XOST, PORT = "0.0.0.0", 1337
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((XOST, PORT))
    srv.listen(10)
    print(f"[ARIA] Server {XOST}:{PORT} da ishga tushdi")

    while True:
        conn, manzil = srv.accept()
        t = threading.Thread(target=mijozni_boshqarish, args=(conn, manzil), daemon=True)
        t.start()

if __name__ == "__main__":
    asosiy()
