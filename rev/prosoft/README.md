# ProSoft v1.0

| Field | Value |
|-------|-------|
| Category | Rev |
| Points | ? |

## Description

> You have the binary of "ProSoft v1.0." It ships in two editions:
> Free and Paid. The paid version includes a secret "vault" with important data.
>
> Your goal: access the paid vault and retrieve the flag.

## Solution

1. Load the binary in **Ghidra** or **IDA Pro**
2. Find the license check / edition gate
3. Patch the binary or extract the hardcoded vault contents
4. Alternatively: find the vault password through static analysis

**Tools:** Ghidra, GDB, `strings`, `objdump`

## Flag

`CHC{...}`
