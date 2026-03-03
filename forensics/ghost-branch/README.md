# Ghost Branch

| Field | Value |
|-------|-------|
| Category | Forensics |
| Points | ? |

## Description

> Kompaniya ofisida bir xodim oddiy **vendor sync** sahifasiga o'xshagan linkni ochganidan keyin,
> tarmoq bir oz sekinlab qoladi. Oradan ko'p o'tmay hammasi yana normal holatga qaytadi.
> Filial gateway'idan olingan qisqa **PCAP** saqlanib qolgan.
>
> Trafik oddiy ofis trafikiga o'xshaydi: kundalik so'rovlar, fon trafiklari va shubhali ko'rinadigan
> narsalar ham bor. Lekin hamma shubhali ko'ringan trafik ham hujum degani emas.
>
> Vazifangiz — aslida nima bo'lganini PCAP ichidan topish: qaysi kompyuter zararlanganini,
> qaysi ichki faylga murojaat qilinganini, ma'lumot qanday chiqarilganini va hujumchining
> session/campaign ID sini tiklash.
>
> **Flag format:** `CHC{sha256_hex}` — qiymatlar `|` bilan qo'shilib SHA-256 olinadi:
> `compromised_hostname|campaign_id|stolen_filename|exfil_start_utc`

**Files:** `src/ghost_branch.pcap`

## Solution

### 1 — Protokollarni ko'rish

```bash
tshark -r ghost_branch.pcap -q -z io,phs
```

DNS, HTTP, SMB, ICMP va boshqa protokollar mavjud.

---

### 2 — HTTP so'rovlar ichidan shubhali so'rovni topish

```bash
tshark -r ghost_branch.pcap -Y "http.request" -T fields \
  -e frame.number -e ip.src -e http.host -e http.request.uri
```

Ko'p normal so'rovlar orasida shubhali bitta ajralib chiqadi:

- **Host:** `vendor-sync-support.com` (tashqi domen)
- **URL param:** `cid=GBR-7Q2A` — campaign/session marker
- **Source IP:** `10.10.20.23`

`10.10.20.23` ni **compromised host candidate** deb belgilaymiz.

---

### 3 — Host mapping (DHCP)

```bash
tshark -r ghost_branch.pcap -Y "dhcp" -V | grep -E "Host Name|Your \(client\) IP address"
```

DHCP orqali `10.10.20.23` → hostname **`BR-WS23`** ekanligini tasdiqlaymiz.

---

### 4 — SMB orqali o'g'irlangan faylni aniqlash

```bash
strings ghost_branch.pcap | grep -F "CREATE Request File="
```

Bir nechta fayl nomi ko'rinadi. Qaysi biri haqiqatan o'qilganini aniqlash uchun:

```bash
tshark -r ghost_branch.pcap -Y "tcp.port==445" -T fields \
  -e frame.number -e ip.src -e ip.dst -e tcp.payload | tail -n 15
```

**Frame tahlili:**

- `SMB2 CREATE Request` → `BranchBudget_2025-Final.xlsx` — source: `10.10.20.23 → 10.10.20.10`
- `SMB2 READ Request` + `SMB2 READ Response` — fayl haqiqatan **o'qilgan** ✓
- `SMB2 CREATE Request` → `Payroll_Q4_Archive.xlsx` — source: `10.10.20.12` — READ yo'q → **tuzoq** ✗

**O'g'irlangan fayl:** `BranchBudget_2025-Final.xlsx`

---

### 5 — DNS ichidan campaign ID qolgan qismlarini topish

```bash
tshark -r ghost_branch.pcap \
  -Y "ip.addr==10.10.20.23 && dns && dns.qry.name" \
  -T fields -e frame.number -e dns.qry.name | grep cid | head -n 5
```

DNS query'lardan:

```
x.001.056.cid91d3.j5tgm2ldmuqgk6dq.cdn-sync-cache.net
x.002.056.cid91d3.n5zhiidtorqwo2lo.cdn-sync-cache.net
x.003.056.cid91d3.m4fem2lmmvxgc3lf.cdn-sync-cache.net
```

`cid91d3` → campaign ID'ning qolgan qismi.

**To'liq Campaign ID:** `GBR-7Q2A-91D3`

---

### 6 — Exfiltration metodi

```bash
tshark -r ghost_branch.pcap \
  -Y 'dns.qry.name contains "cdn-sync-cache.net"' \
  -T fields -e frame.number -e ip.src -e dns.qry.name | head -30
```

`x.001`, `x.002`, `x.003` ko'rinishidagi ketma-ket chunk'lar DNS subdomain ichiga yashirilgan.

**Exfil metodi:** DNS tunneling (chunked subdomain labels)

---

### 7 — Birinchi exfil chunk vaqti (UTC)

```bash
tshark -r ghost_branch.pcap \
  -Y 'ip.src==10.10.20.23 && dns.qry.name matches "^x\\."' \
  -T fields -e frame.time_epoch -e frame.number -e dns.qry.name | head -1
```

- **Epoch:** `1768377623.353331000` → frame `2499`

```bash
date -u -d @1768377623 +%Y-%m-%dT%H:%M:%SZ
```

**Exfil start UTC:** `2026-01-14T08:00:23Z`

---

### 8 — Topilmalar

| Field | Value |
|-------|-------|
| Compromised hostname | `BR-WS23` |
| Compromised IP | `10.10.20.23` |
| Stolen file | `BranchBudget_2025-Final.xlsx` |
| Campaign ID | `GBR-7Q2A-91D3` |
| Exfil method | DNS tunneling (chunked subdomain labels) |
| Exfil start UTC | `2026-01-14T08:00:23Z` |

Flag string (pipe-separated):
```
BR-WS23|GBR-7Q2A-91D3|BranchBudget_2025-Final.xlsx|2026-01-14T08:00:23Z
```

## Flag

`CHC{BR-WS23_GBR-7Q2A-91D3_BRANCHBUDGET_2025-FINAL.XLSX_2026-01-14T08:00:23Z}`
