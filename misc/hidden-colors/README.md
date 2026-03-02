# Hidden Colors

| Field | Value |
|-------|-------|
| Category | Misc |
| Points | ? |

## Description

> We seized an image from a suspect. It looks like an ordinary picture,
> but we suspect they used multiple layers of security to hide information.
> Can you find the hidden message?

## Solution

### Step 1 — Find the Hidden Archive
```bash
binwalk chill.png
# or:
unzip chill.png   # PNG ignores appended data; unzip reads ZIP central directory at end
```
A password-protected ZIP archive is appended to the PNG.

### Step 2 — Crack the ZIP Password
```bash
zip2john secret.zip > crack.txt
john --wordlist=/usr/share/wordlists/rockyou.txt crack.txt
# Password: jakeamor
```

### Step 3 — Extract the Image
```bash
unzip -P jakeamor secret.zip
# Extracts: kinder_surprise.png
```

### Step 4 — LSB Steganography
Open `kinder_surprise.png` in **StegSolve** and check each color plane:
- **Red Bit 0:** `CHC{`
- **Green Bit 0:** `b4s1c_st3go`
- **Blue Bit 0:** `_m4st3r_2026}`

Concatenate to get the full flag.

## Flag

`CHC{b4s1c_st3go_m4st3r_2026}`
