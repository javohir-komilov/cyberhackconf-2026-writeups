# Obfuscated BATCH

| Field | Value |
|-------|-------|
| Category | Rev |
| Points | ? |

## Description

> Reverse engineer the obfuscated Windows batch script.

## Solution

*See [writeup/WriteUp.pdf](writeup/WriteUp.pdf) for the full solution.*

**Summary:** Deobfuscate the `.batctf` file by tracing variable substitutions,
escape sequences, and `FOR` loop tricks commonly used in batch obfuscation.
Tools like [de4bat](https://github.com/digitalbond/de4bat) or manual tracing
can be used.

## Flag

`CHC{...}`
