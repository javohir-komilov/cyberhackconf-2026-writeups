# YARA

| Field | Value |
|-------|-------|
| Category | Forensics |
| Points | ? |

## Description

> Analyze the YARA rule and answer 7 questions about the malware it detects.
> Quiz-style challenge answered via an interactive server.

## Questions & Answers

| # | Question | Answer |
|---|----------|--------|
| 1 | File signature in the YARA rule | `0x5A4D` |
| 2 | SHA256 hash of matching file | `7d14b98cdc1b898bd0d9be80398fc59ab560e8c44e0a9dedac8ad4ece3d450b0` |
| 3 | MITRE ATT&CK ID for malware activity | T1486 |
| 4 | Nickname of author of 2 matching Sigma rules | frack113 |
| 5 | Extension of encrypted files | `.PLAY` |
| 6 | Email in ReadMe.txt | `boitelswaniruxl@gmx.com` |
| 7 | Other alias for this malware | PlayCrypt |

## Solution

1. **Q1** — `uint16(0)` in YARA checks bytes at offset 0 → `0x5A4D` = MZ header (PE executable)
2. **Q2** — Search [YARAify](https://yaraify.abuse.ch/search/) with `yarahub_reference_md5 = "0ba1d5a26f15f5f7942d0435fa63947e"` or use Hybrid Analysis YARA search
3. **Q3** — Submit file to sandbox (any.run) → T1486: Data Encrypted for Impact
4. **Q4** — VirusTotal → Crowdsourced Sigma Rules → both written by `frack113`
5. **Q5** — Sandbox analysis → encrypted files have `.PLAY` extension
6. **Q6** — [any.run task](https://app.any.run/tasks/1841fab9-8d80-4079-abd9-7f8e5003825d) → Files → ReadMe.txt
7. **Q7** — [ThreatFox](https://threatfox.abuse.ch/browse/malware/win.play/) or Malpedia → alias: **PlayCrypt**

**Malware family:** PLAY ransomware (alias PlayCrypt)

## Flag

Multiple flags, one per correct question answer.
