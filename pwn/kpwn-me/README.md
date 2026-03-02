# kpwn_me

| Field | Value |
|-------|-------|
| Category | Pwn |
| Points | ? |

## Description

> A kernel pwn challenge.
>
> Player files: `bzImage`, `initramfs.cpio.gz`, `run.sh`

## Solution

> simple race condition in the kernel abusing from userfaultd


**Attack vector:** Race condition in the kernel module abusing `userfaultfd`.

**Steps:**
1. Reverse engineer the kernel module from the provided `initramfs.cpio.gz`
2. Identify the race condition vulnerability
3. Use `userfaultfd` to win the race and escalate privileges
4. Read the flag from `/root/flag.txt` or similar

**Tools:** `qemu`, `pwndbg`, `userfaultfd`, kernel exploit primitives

## Flag

`CHC{...}`
