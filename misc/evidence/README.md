# Evidence

| Field | Value |
|-------|-------|
| Category | Misc |
| Points | ? |

## Description

> Scientists at AI Research Lab were working on a system that automatically
> analyzes digital evidence using AI.
>
> The project has been officially declared "unfinished."
>
> PNG files are corrupted. CRCs are wrong. Chunks are shifted.
>
> One file is much larger than it should be.
>
> Someone tried to restore the server and hide their data.

## Solution

Analyze the provided PNG files:

1. Use `pngcheck` or a hex editor to identify corrupted chunks and wrong CRCs
2. Repair PNG headers/CRCs manually or with `pngfix`
3. The oversized file contains hidden data — check with `binwalk` or `strings`
4. Extract the hidden content to reveal the flag

**Tools:** `pngcheck`, `binwalk`, `HxD`/`hexedit`, `zlib` decompress

## Flag

`CHC{s3n!n5_!pn9_f4hl1n6-@ni14qndL}`
