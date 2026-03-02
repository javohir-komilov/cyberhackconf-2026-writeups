# An Innocent Employee

| Field | Value |
|-------|-------|
| Category | Forensics |
| Points | ? |

## Description

> Our employee got hacked and claims he didn't do anything wrong!
> Can you find out how he was hacked?
>
> This is a quiz-style challenge with 7 questions answered via an interactive server.

## Questions & Answers

| # | Question | Answer | Points |
|---|----------|--------|--------|
| 1 | Application where the conversation took place | Discord | 100 |
| 2 | Attacker and victim usernames (Format: @attacker:@victim) | johnysainz_94219:bob_12331 | 300 |
| 3 | When was the malicious link sent? (year-mm-dd hh:mm:ss UTC) | 2025-12-18 16:00:45 UTC | 200 |
| 4 | Required password | yCyU9NsRj2 | 200 |
| 5 | File sharing service used | mega.nz | 100 |
| 6 | SHA256 hash of the malicious file | 8f16da672b72afa99e534d022b945bdc8a4ea1083d09ba7930df2dd163eb3bb8 | 50 |
| 7 | Malware family | Infostealer | 50 |

## Solution

1. Open the disk image in **FTK Imager** or Autopsy
2. **Q1** — Check installed/recent apps → find Discord
3. **Q2** — Navigate to Discord cache: `C:\Users\bob\AppData\Roaming\discord\Cache\Cache_Data`
   - Use **ChromeCacheViewer** (same format as Chrome cache)
   - Find `50.json` → dialog between `johnysainz_94219` and `bob_12331`
4. **Q3** — Timestamp of the malicious link message: `2025-12-18 16:00:45 UTC`
5. **Q4** — Bob said he "noted" the password → check **Microsoft Sticky Notes**
   - File: `%AppData%\Microsoft\Sticky Notes\plum.sqlite` + `plum.sqlite-wal`
   - Password: `yCyU9NsRj2`
6. **Q5** — Unlock Pastebin link with the password → mega.nz link inside
7. **Q6** — Download the file → `sha256sum` → hash as above
8. **Q7** — Search hash on VirusTotal → **Infostealer**

## Flag

Multiple flags, one per correct question answer.
