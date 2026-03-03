# Router

| Field | Value |
|-------|-------|
| Category | Forensics |
| Points | ? |

## Description

> Do you really think your router is secure?
>
> Quiz-style challenge — 6 questions answered via an interactive server.
> You are given a router firmware dump to analyze.

**Files:** `router.7z` (firmware dump, ~19MB — excluded from git due to binary size)

## Questions & Answers

| # | Question | Answer | Points |
|---|----------|--------|--------|
| 1 | OS version of the router | 23.05.4 | 50 |
| 2 | CVE number of the exploited vulnerability | CVE-2022-28927 | 50 |
| 3 | IP address of the attacker's machine | 156.238.233.47 | 50 |
| 4 | Program configuration modified for persistence | dropbear | 100 |
| 5 | Host hijacked by the attacker | portal.r3.internal | 100 |
| 6 | Host used to serve malicious artifacts | nimble-bonbon-d941a8.netlify.app | 200 |

## Solution

1. **Q1** — Check `/etc/banner` → OS version
2. **Q2** — CVE-2022-28927 affects OpenWrt's Subconverter
3. **Q3** — Check `root/subconverter/cache/dad176d5807526bf19069ecce4f14bfe`
4. **Q4** — Find modified config in Dropbear's authorized_keys
5. **Q5** — Check `/etc/config/dhcp` → hijacked hostname
6. **Q6** — Extract `www/` folder, add `portal.r3.internal` to `/etc/hosts`,
   run local HTTP server → deobfuscate `bootstrap.min.js`
   (tool: [js deobfuscator](https://github.com/pxx917144686/js))

**Tools:** FTK Imager, Wireshark, file analysis utilities

## Flag

Multiple flags, one per correct question answer.
