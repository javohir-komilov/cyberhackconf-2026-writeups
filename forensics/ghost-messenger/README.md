# The Ghost Messenger

| Field | Value |
|-------|-------|
| Category | Forensics |
| Points | ? |

## Description

> Our secret agent vanished unexpectedly, taking critical information with them.
> The only thing left behind is a network traffic capture from their computer.
> Our team couldn't find the necessary information — but we're certain the agent
> used covert communication channels to hide a secret message.
>
> **Hint (from HTTP headers):** In a multiplayer game, when ping is low,
> actions are more precise.

## Solution

### Step 1 — String Extraction
```bash
strings "The Ghost Messenger.pcap" | grep -i "Content-Security-Policy" | sort | uniq
```
One unique CSP header stands out and hints at **UDP traffic**.

### Step 2 — Find Telegram Links
```bash
strings "The Ghost Messenger.pcap" | grep -i "t.me" | sort | uniq
```
Multiple identical Telegram links appear, plus one unique truncated `t.me/user...` link.

### Step 3 — Wireshark Deep Search
- Open in Wireshark → `Ctrl+F`
- Search: **Packet bytes** → **Regular Expression** → `t.me/user`
- Find the packet → right-click → **Follow > UDP Stream**

### Step 4 — Retrieve Flag
Following the UDP stream reveals the full Telegram channel URL.
Navigate to the channel to find the flag posted there.

## Flag

`CHC{0p3n_7h3_534l_r34d_7h3_p47h}`
