# macOS Sandbox Bypass via Shared Directory

## Problem

macOS sandbox on recent versions (15.x) blocks read access to `~/Documents/` and `~/Desktop/` for files created by other applications (Excel, WeChat, etc.). Files appear to exist but return `Operation not permitted` when read via Python/terminal.

## Solution

Use `~/.hermes/shared/` as a permanent sandbox-bypass directory:

1. Create: `mkdir -p ~/.hermes/shared/`
2. Add to Finder sidebar for easy access (user drags folder icon to Favorites)
3. User places all work files (Excel, PDF, images) here before starting tasks
4. This directory is NOT affected by iCloud optimization

## Verification

```bash
test -r ~/.hermes/shared/some_file.xlsx && echo "readable"
```

## Important

- `~/.hermes/shared/` is permanent — not auto-cleaned
- `~/.hermes/cache/` IS auto-cleaned — don't store work files there
- The user may also mirror files between `~/Documents/` and `~/.hermes/shared/`
