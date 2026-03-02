# Ghost Branch

| Field | Value |
|-------|-------|
| Category | Forensics |
| Points | ? |

## Description

> After an employee opened a link that looked like an ordinary vendor sync page,
> the network slowed briefly before returning to normal. A short PCAP from the
> branch gateway was captured.
>
> The traffic looks like everyday office traffic — routine requests, background
> noise, and a few suspicious-looking events (scan-like activity, odd pings).
> But not everything suspicious is an attack.
>
> Your task: reconstruct what actually happened from inside the PCAP.
> Identify which host was compromised, which internal file was accessed,
> how data was exfiltrated, and piece together the attacker's session/campaign ID.
>
> **Flag format:** `CHC{COMPROMISED-HOSTNAME_CAMPAIGN-ID_STOLEN-FILENAME_EXFIL-START-UTC}`

## Solution

Analyze the PCAP with **Wireshark** / **tshark**:

1. Identify the compromised host by finding unusual outbound connections
2. Find the internal file accessed by the attacker
3. Determine the exfiltration method and start time (UTC)
4. Extract the campaign/session ID from attacker traffic

Combine the four values in order (all UPPERCASE):
`COMPROMISED-HOSTNAME_CAMPAIGN-ID_STOLEN-FILENAME_EXFIL-START-UTC`

**Recommended tools:** Wireshark, tshark, strings, Python

## Flag

`CHC{BR-WS23_GBR-7Q2A-91D3_BRANCHBUDGET_2025-FINAL.XLSX_2026-01-14T08:00:23Z}`
