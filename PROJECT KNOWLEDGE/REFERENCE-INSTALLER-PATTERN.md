# Installer-as-Codebase Pattern — Architecture Handoff

> **Purpose of this document.** This is a complete technical handoff describing the **installer-as-codebase pattern** that the user (Nick) uses across all of his Python programs. The next AI agent building a new program for Nick MUST follow this pattern. This document is generic — it describes the **pattern**, not any specific program's contents. Apply it to whatever new program you're building.
>
> **Reference implementation.** The mature reference implementation is `install8.py` in the Blaze MIS Audit Pro project — 48 tracked files, ~272 lines of installer logic, all source embedded as base64. Read this document end-to-end before writing the first line of the new installer.

---

## 1. The pattern in one sentence

**A single Python file holds the entire codebase as base64 strings, plus SHA-256 hashes for drift detection, plus a small `main()` workflow that writes the files to disk surgically and only when they've changed.**

That one file is both the installer (first run on a fresh machine) and the updater (every subsequent run after edits). The user never edits files in `src/`, `static/`, or `templates/` directly — they edit the embedded base64 blobs inside the installer, re-run it, and the installer overwrites only the files whose hashes no longer match. The on-disk codebase is therefore a **deterministic artifact** of the installer; the installer is the source of truth.

---

## 2. Why this pattern exists

Nick runs his programs as local Flask apps on Windows. He has:

- No git workflow
- No CI/CD
- No developer IDE in the active loop (he uses Claude / Claude Code to edit)
- A working program he must not regress

The friction without the pattern: editing a program means hunting through 40+ files across `src/`, `static/`, `templates/`, etc., remembering which were touched, manually copying them to the install directory, and hoping nothing was missed. **Every edit risks regressions and partial updates.**

The friction with the pattern: there is exactly **one file** that the user and the AI agent ever touch. Update the relevant base64 blob and its matching SHA-256, save, run `python install.py`, and the installer surgically writes only the changed files. Everything else is left untouched. **Zero drift, zero forgotten files, zero partial updates.**

When Nick says *"I only have to update the install script and it takes care of the rest"* — this is what he means. **It is the deliberate, intentional architecture. An AI agent that edits files in `src/` directly is bypassing the system and will cause drift.**

---

## 3. File layout — anatomy of the installer

The installer file (e.g. `install.py`, `install8.py`, etc.) is divided into **5 distinct regions** in this order:

| Region | Lines (approx) | Contents |
|---|---|---|
| **1. Header** | 1–10 | Shebang, imports, `SCRIPT_VERSION`, `PROFILE_HANDLE`, `HERE` |
| **2. `FILES` dict** | 10–60 | The entire codebase as base64 strings, one entry per line |
| **3. `HASHES` dict** | 60–110 | SHA-256 of each decoded file's bytes, same keys as `FILES` |
| **4. Constants & helpers** | 110–130 | `DIRS`, `BLANK_INITS`, `PACKAGES`, `PROTECTED`, color helpers, `_cred_specs()`, `SESSION_INIT_CONTENT` |
| **5. Logic & `main()`** | 130–end | `detect_mode()`, `scan_files()`, `write_files()`, the 6-step `main()` workflow |

### 3.1 Region 1 — Header

```python
#!/usr/bin/env python3
"""
PROGRAM_NAME — self-contained installer / updater.
Run: python install.py
"""
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROFILE_HANDLE: str = "nicktat"   # Used for credential filename suffixes
SCRIPT_VERSION:  str = "2026-05-26-INITIAL-V1"   # Format: YYYY-MM-DD-DESCRIPTOR-VN
HERE:            Path = Path(__file__).resolve().parent   # Per pathlib rule
```

**Critical:** `HERE` is anchored to `Path(__file__).resolve().parent`. Never `Path.cwd()`. This is project rule #3 ("Pathlib is law"). The installer must work identically regardless of which directory it is launched from.

### 3.2 Region 2 — The `FILES` dict

```python
FILES: dict[str, str] = {
    'Launcher.py':                'IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoj...',  # ~18 KB
    'run.py':                     '...',                                   #  ~1.5 KB
    'settings.json':              '...',                                   #   ~600 B
    'src/app.py':                 '...',
    'src/api/main_api.py':        '...',                                   # potentially 200KB+ on ONE line
    # ... one entry per file in the program ...
    'templates/index.html':       '...',
}
```

**Critical details:**
- **Keys are relative paths** (POSIX-style forward slashes, even on Windows — `Path` handles the conversion).
- **Values are single base64 strings.** No line breaks. No chunking. A 220 KB file is one ~300,000-character line. The reference implementation has lines that long. **Do not be alarmed by lines that scroll for screens** — this is correct.
- **One key per file**, value on the same line. Use vertical-align padding for readability:
  ```python
  'src/app.py':                 '<b64>',
  'src/api/main_api.py':        '<b64>',
  ```
- The dict is `dict[str, str]` typed. Python 3.10+ syntax (per project rule #4).

### 3.3 Region 3 — The `HASHES` dict

```python
HASHES: dict[str, str] = {
    'Launcher.py':                'a93b...c2f1',  # SHA-256 hex digest of DECODED bytes
    'run.py':                     '...',
    # ... same 40+ keys as FILES, in the same order ...
    'templates/index.html':       '092e0586c4e31dae7af14c7746c3b0c0f36820249f5b9b0fa1c85b2df7f3c511',
}
```

**Critical details:**
- **Same keys as `FILES`**, in the same order (for diffability).
- **Each value is the SHA-256 hex digest of the decoded file bytes** — i.e. `sha256(base64.b64decode(FILES[path])).hexdigest()`.
- When updating a file, **both** `FILES[path]` and `HASHES[path]` must be updated. Updating only one will either skip the file (hash matches old version) or report a drift error.

### 3.4 Region 4 — Constants and helpers

```python
DIRS: list[str] = [
    'src', 'src/api', 'src/core', 'src/utils', 'src/integrations',
    'static', 'static/js', 'static/css',
    'templates',
    'config', 'config/tokens', 'config/google_creds',
    'secrets', 'reports', 'logs',
]   # Created with mkdir(parents=True, exist_ok=True) in step 2

BLANK_INITS: list[str] = [
    'src/__init__.py',
    'src/api/__init__.py',
    'src/core/__init__.py',
    'src/utils/__init__.py',
    'src/integrations/__init__.py',
]   # Empty __init__.py files — written if missing, NOT tracked in HASHES

PACKAGES: list[str] = [
    'flask>=3.0',
    'pandas>=2.0',
    'requests>=2.31',
    # ... pinned to >= minor version, not exact ==, so pip can upgrade ...
]   # pip-installed in step 6

PROTECTED: set[str] = {
    'secrets/sync_keys.json',
    'config/tokens/token_PROFILE.json',
    'config/google_creds/credentials_PROFILE.json',
    'config/blaze_configs/blaze_config_PROFILE.json',
    'PROGRAM_CREDENTIALS.json',
}   # NEVER overwritten by write_files() — credential files preserved across re-runs

SESSION_INIT_CONTENT: str = """\
from src.session.manager import SessionManager
session: SessionManager = SessionManager()

def init_session(app) -> None:
    @app.teardown_appcontext
    def _close(exc=None):
        try: session.close()
        except Exception: pass

__all__ = ["session", "init_session"]
"""   # Special-case literal — written as text, not base64
SESSION_INIT_HASH: str = hashlib.sha256(SESSION_INIT_CONTENT.encode()).hexdigest()

# Color print helpers
def _ok(m: str)   -> None: print(f"\033[32m  ✓ {m}\033[0m")
def _warn(m: str) -> None: print(f"\033[33m  ⚠ {m}\033[0m")
def _err(m: str)  -> None: print(f"\033[31m  ✗ {m}\033[0m")
def _dim(m: str)  -> None: print(f"\033[90m    {m}\033[0m")

def _cred_specs() -> dict[str, dict]:
    """Placeholder credential JSON for first-run bootstrap."""
    return {
        'config/blaze_configs/blaze_config_PROFILE.json': {
            'mis': {'username': 'REPLACE', 'password': 'REPLACE'},
            'blaze': {'email': 'REPLACE', 'password': 'REPLACE'},
        },
        # ... one entry per PROTECTED credential file ...
    }
```

### 3.5 Region 5 — Logic and `main()`

This is where the actual installer logic lives. See sections 4–6 below for the full implementation.

---

## 4. Base64 encoding mechanics — the heart of the pattern

### 4.1 How to encode a file INTO the installer

```python
import base64, hashlib
from pathlib import Path

src_file = Path('src/app.py')
content_bytes = src_file.read_bytes()                            # Read as BYTES, not text
b64_string    = base64.b64encode(content_bytes).decode('ascii')  # Encode → decode to str
sha_string    = hashlib.sha256(content_bytes).hexdigest()        # Hash the DECODED bytes

# Now patch into installer:
# FILES['src/app.py'] = b64_string
# HASHES['src/app.py'] = sha_string
```

**Key invariants:**
- Always read as bytes (`.read_bytes()`), never as text. Text would mangle line endings on Windows and corrupt binary files.
- `base64.b64encode()` returns bytes; call `.decode('ascii')` to get a `str` suitable for inclusion in a Python string literal.
- Hash the **decoded bytes**, not the base64 string. The installer verifies disk content against this hash.

### 4.2 How to decode a file OUT of the installer (during install/update)

```python
encoded = FILES['src/app.py']
decoded_bytes = base64.b64decode(encoded)
Path(install_dir / 'src/app.py').write_bytes(decoded_bytes)
```

Round-trip guarantee: `base64.b64decode(base64.b64encode(b))` == `b` for any bytes `b`. The installer relies on this being exact.

### 4.3 How to verify a file matches the embedded version

```python
disk_bytes = Path(install_dir / 'src/app.py').read_bytes()
disk_hash  = hashlib.sha256(disk_bytes).hexdigest()
expected   = HASHES['src/app.py']
is_drifted = (disk_hash != expected)
```

If `is_drifted` is `True`, the file on disk has been modified since the last install and needs to be rewritten from `FILES['src/app.py']`. This is what enables surgical updates.

### 4.4 Why not zip / why not pickle / why not pyz?

Base64 was chosen because:
1. **One file, no external archives.** The whole program is one `.py` file Nick can email himself, copy to a USB stick, or paste into a chat.
2. **Plain-text diffable.** Each file is one line; an AI agent can `str_replace` a single line without touching others.
3. **No binary dependencies in the installer.** Base64 is in the Python stdlib.
4. **AI-editable.** Claude can `str_replace` `FILES['path']: '<old_b64>'` → `FILES['path']: '<new_b64>'` in one operation.

Trade-offs:
- The installer file is ~33% larger than the raw source (base64 overhead). Acceptable.
- Editing the installer requires base64 decode/encode steps. Mitigated by the agent workflow (§7).

---

## 5. The 6-step `main()` workflow

The installer runs a fixed 6-step sequence on every invocation. The same code path handles both **first-time install** (fresh machine, no files exist) and **update** (program already installed, only some files have changed).

```python
def main() -> None:
    print(f"\n  PROGRAM_NAME installer  ·  {SCRIPT_VERSION}")
    print("  " + "=" * 60)

    install_dir = HERE   # Install in the same directory as the script

    # [1/6] Python version check
    v = sys.version_info
    print(f"\n[1/6]  Checking Python version  ({v.major}.{v.minor}.{v.micro})")
    if v < (3, 10):
        _err("Python 3.10+ required.")
        sys.exit(1)
    _ok(f"Python {v.major}.{v.minor} OK")

    # [2/6] Directory creation
    print("\n[2/6]  Ensuring directories")
    new_dirs = 0
    for d in DIRS:
        p = install_dir / d
        if not p.exists(): new_dirs += 1
        p.mkdir(parents=True, exist_ok=True)
    _ok(f"{len(DIRS)} directories ready ({new_dirs} new)")

    # [3/6] File validation + surgical write
    print("\n[3/6]  Validating files")
    mode = detect_mode(install_dir)
    nf, cf, uf = scan_files(install_dir)
    print(f"       Mode      : {mode}")
    print(f"       Unchanged : {len(uf)} files")
    print(f"       New       : {len(nf)} file(s)")
    for p in nf: _dim(f"+ {p}")
    print(f"       Updated   : {len(cf)} file(s)")
    for p in cf: _dim(f"~ {p}")
    write_files(install_dir, nf, cf, uf, mode)

    # Write BLANK_INITS if missing
    for blank in BLANK_INITS:
        p = install_dir / blank
        if not p.exists(): p.write_text("", encoding="utf-8")

    # Copy settings.json → config/settings.json if config copy doesn't exist
    if (install_dir / 'settings.json').exists() and not (install_dir / 'config/settings.json').exists():
        shutil.copy(install_dir / 'settings.json', install_dir / 'config/settings.json')

    # [4/6] Credentials handling — see §6 for full details
    print("\n[4/6]  Handling credential files")
    handle_credentials(install_dir)

    # [5/6] Critical files smoke check
    print("\n[5/6]  Verifying critical files")
    critical = [
        'run.py', 'Launcher.py', 'src/app.py',
        'src/session/__init__.py', 'src/api/main_api.py',
        'templates/index.html', 'static/js/main.js',
    ]
    missing = [c for c in critical if not (install_dir / c).exists()]
    if missing:
        for m in missing: _warn(f"missing: {m}")
    else:
        _ok(f"{len(critical)} critical files present")

    # [6/6] pip dependency install
    print("\n[6/6]  Installing/verifying dependencies")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", *PACKAGES],
        capture_output=True, text=True,
    )
    # Parse "Successfully installed" lines (skip "already satisfied")
    for line in result.stdout.splitlines():
        if line.startswith("Successfully installed"):
            _ok(line.strip())
    if result.returncode != 0:
        for line in result.stderr.splitlines():
            if "error" in line.lower(): _err(line.strip())

    # Final prompt
    print("\n  " + "=" * 60)
    _ok(f"Update complete  ({len(cf)} file(s) updated, {len(uf)} unchanged)")
    print("  " + "=" * 60)
    print(f"\n  To launch:  python Launcher.py\n")
    ans = input("  Launch the program now? [y/N] ").strip().lower()
    if ans == 'y':
        os.chdir(install_dir)
        subprocess.run([sys.executable, "Launcher.py"])
```

### 5.1 `detect_mode()` — install vs update

```python
def detect_mode(install_dir: Path) -> str:
    """Return 'update' if the program is already installed, else 'install'."""
    return "update" if (install_dir / "src" / "app.py").exists() else "install"
```

The sentinel file is `src/app.py` (the Flask app factory). If it exists, the program is already installed; the installer will write only changed files. If it doesn't, this is a fresh machine and the installer writes everything.

### 5.2 `scan_files()` — bucket-sort into new / changed / unchanged

```python
def scan_files(install_dir: Path) -> tuple[list[str], list[str], list[str]]:
    """Return (new_files, changed_files, unchanged_files)."""
    nf: list[str] = []
    cf: list[str] = []
    uf: list[str] = []
    # Include the special session __init__.py
    all_paths = list(HASHES.items()) + [("src/session/__init__.py", SESSION_INIT_HASH)]
    for rel_path, expected_hash in all_paths:
        if rel_path in PROTECTED:
            continue   # Never touched
        disk_path = install_dir / rel_path
        if not disk_path.exists():
            nf.append(rel_path)
        else:
            disk_hash = hashlib.sha256(disk_path.read_bytes()).hexdigest()
            if disk_hash != expected_hash:
                cf.append(rel_path)
            else:
                uf.append(rel_path)
    return nf, cf, uf
```

### 5.3 `write_files()` — the surgical writer

```python
def write_files(
    install_dir: Path,
    nf: list[str],
    cf: list[str],
    uf: list[str],
    mode: str,
) -> None:
    """Write new + changed files. Install mode also rewrites unchanged for safety."""
    targets = nf + cf if mode == "update" else nf + cf + uf
    for rel_path in targets:
        if rel_path in PROTECTED:
            continue
        dest = install_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel_path == "src/session/__init__.py":
            dest.write_text(SESSION_INIT_CONTENT, encoding="utf-8")
        else:
            dest.write_bytes(base64.b64decode(FILES[rel_path]))
```

**Why a special case for `src/session/__init__.py`?** It's small, almost never changes, and needs to be human-readable inside the installer (so the agent can see the singleton pattern at a glance). Encoding a 10-line file as base64 would be a readability tax for zero benefit. Use this special case for any tiny, rarely-changing files you want to inline as plain text — but use it sparingly (one or two files max).

---

## 6. Credentials handling (step 4) — the safety-critical step

Credential files contain secrets. They must **never be overwritten** by the installer, even if it has a copy embedded. Step 4 implements three fallback paths:

### 6.1 Path A — Unified credentials file split

Users may drop a single `PROFILE_credentials_unified.json` next to the installer, containing all secrets in one nested JSON:

```json
{
  "mis":          { "username": "...", "password": "..." },
  "blaze":        { "email": "...", "password": "..." },
  "google_oauth": { "installed": { ... } },
  "google_token": { "token": "...", "refresh_token": "..." },
  "sync_keys":    { "store_a": "...", "store_b": "..." }
}
```

The installer reads this file, splits it into the individual credential files the program expects, and writes each one **only if it doesn't already exist**. Pseudocode:

```python
def split_unified(install_dir: Path) -> bool:
    """Look for unified file in install_dir or alongside the script. Split if found."""
    for candidate in (install_dir, HERE):
        unified = candidate / f"{PROFILE_HANDLE}_credentials_unified.json"
        if unified.exists():
            data = json.loads(unified.read_text())
            mapping = {
                'config/blaze_configs/blaze_config_PROFILE.json': {
                    'mis': data.get('mis'), 'blaze': data.get('blaze'),
                },
                'config/google_creds/credentials_PROFILE.json': data.get('google_oauth'),
                'config/tokens/token_PROFILE.json':            data.get('google_token'),
                'secrets/sync_keys.json':                       data.get('sync_keys'),
            }
            for rel_dest, content in mapping.items():
                if content is None: continue
                dest = install_dir / rel_dest
                if dest.exists():
                    _dim(f"{rel_dest} exists, skipped")
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(content, indent=2))
                _ok(f"wrote {rel_dest}")
            return True
    return False
```

**Safety invariants:**
1. **Never overwrite existing credential files.** The `if dest.exists(): continue` guard is non-negotiable.
2. **The unified file is read but never deleted.** Users can re-run the installer freely without losing their secrets.
3. **The unified file may live in either `install_dir` or `HERE`.** Both are checked.

### 6.2 Path B — Legacy per-file fallback

If no unified file is found, look for individual credential files alongside the script (`HERE`) using the various casing permutations of `PROFILE_HANDLE`:

```python
for variant in (PROFILE_HANDLE, PROFILE_HANDLE.lower(), PROFILE_HANDLE.upper()):
    legacy = HERE / f"blaze_config_{variant}.json"
    if legacy.exists():
        dest = install_dir / f"config/blaze_configs/blaze_config_{PROFILE_HANDLE}.json"
        if not dest.exists():
            shutil.copy(legacy, dest)
```

### 6.3 Path C — Placeholder bootstrap

If neither A nor B yields a credential file, write a placeholder JSON with `"REPLACE-"` markers so the user knows what to fill in:

```python
TO_FILL: list[str] = []
for rel_dest, placeholder in _cred_specs().items():
    dest = install_dir / rel_dest
    if dest.exists(): continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(placeholder, indent=2))
    TO_FILL.append(rel_dest)
if TO_FILL:
    _warn("Credential files need to be filled in:")
    for p in TO_FILL: _dim(f"  {p}")
```

### 6.4 The `PROTECTED` set — final safety net

Even if a future code change accidentally tries to include a credential file in `FILES`, the `PROTECTED` set is checked in both `scan_files()` and `write_files()`. Any path in `PROTECTED` is skipped unconditionally. **This means no credential ever flows through the base64 encoding step, so no credential is ever leaked through the installer file itself.**

---

## 7. The AI agent edit workflow (the critical part)

This is the workflow every AI agent (Claude, Claude Code, whoever comes next) MUST follow when editing the program through its installer.

> Scenario: User says **"fix the brand dropdown in `static/js/main.js`"**.

### 7.1 Step-by-step

1. **Read the embedded version, not the disk version.** The disk file may already be drifted. Decode `FILES['static/js/main.js']` with `base64.b64decode` to get the canonical current contents.

2. **Make the surgical edit** to the decoded text. Follow Nick's project rules — pathlib, type hints, hybrid logging, surgical edits only.

3. **Re-encode** the modified bytes:
   ```python
   new_b64 = base64.b64encode(new_bytes).decode('ascii')
   ```

4. **Re-hash** the modified bytes:
   ```python
   new_sha = hashlib.sha256(new_bytes).hexdigest()
   ```

5. **Update both dicts in the installer** via two `str_replace` operations — one for the `FILES['static/js/main.js']` line, one for the `HASHES['static/js/main.js']` line. **Do not rewrite the installer from scratch.**

6. **Bump `SCRIPT_VERSION`** to a new identifier reflecting the change. Format: `YYYY-MM-DD-DESCRIPTOR-VN` (e.g. `"2026-05-26-BRAND-DROPDOWN-FIX-V2"`).

7. **Validate Python syntax:**
   ```bash
   python3 -c "import ast; ast.parse(open('install.py').read()); print('OK')"
   ```

8. **Roundtrip-verify the change:** decode `FILES[path]` again and confirm the edit is present in the decoded text AND that `sha256(decoded) == HASHES[path]`.

9. **Deliver only the changed installer** to the user. They run `python install.py`, the installer detects the changed file, writes it surgically, and the program is updated.

### 7.2 Anti-patterns to avoid

- ❌ **Editing files in `src/` or `static/` directly without updating the installer.** The next `install.py` run will overwrite your edit. The user will report "the bug came back" and you will have wasted a session.
- ❌ **Updating `FILES` without updating `HASHES` (or vice versa).** The installer will either skip the file (hash matches old version) or report drift.
- ❌ **Forgetting to bump `SCRIPT_VERSION`.** The user uses it to confirm a new build is actually running. If you forget, they will report "I ran the new installer but nothing changed" — and the version string is the only way to be sure.
- ❌ **Rewriting the entire `FILES` dict from scratch.** Use targeted `str_replace` on the specific entries. Rewriting risks reordering keys, dropping entries, or corrupting unrelated base64 blobs.
- ❌ **Touching `PROTECTED` credential files.** They are skipped for a reason. Editing them through the installer would leak secrets into the installer file itself, which then gets shared in chat / committed to git / emailed.
- ❌ **Adding a new file to `src/` without adding it to BOTH `FILES` and `HASHES`.** The installer will not write it on a fresh install, and on the next update the new file will be invisible.
- ❌ **Using a stale installer as the base.** Always work from `/mnt/user-data/outputs/<current_installer>.py`, never from `/mnt/project/`. Stale bases cause regressions when newer fixes are silently overwritten.
- ❌ **Putting the user's secrets in `FILES`.** The unified credentials file pattern (§6) is the right way to deliver secrets; the installer just splits them. Never embed secrets as base64 in the installer.

---

## 8. Adding a brand-new file to the program

When introducing a new module (e.g. `src/utils/new_helper.py`):

1. Write the file contents.
2. Compute `b64 = base64.b64encode(content_bytes).decode('ascii')`.
3. Compute `sha = hashlib.sha256(content_bytes).hexdigest()`.
4. Add a new line to `FILES` in the installer: `'src/utils/new_helper.py': '<b64>',`
5. Add a matching line to `HASHES` in the installer: `'src/utils/new_helper.py': '<sha>',`
6. If the file lives in a directory not in `DIRS`, add the directory to `DIRS`.
7. If the file is a critical-boot file (one the launcher imports immediately), add it to the `critical` list in step 5 of `main()`.
8. Bump `SCRIPT_VERSION`.
9. Validate syntax + roundtrip.

The installer treats new files identically in install mode (writes them) and update mode (`scan_files` reports them as `nf` since the path doesn't exist on disk, and `write_files` creates parent directories with `mkdir(parents=True, exist_ok=True)`).

---

## 9. Helper utility — re-encoding files in bulk

For the initial creation of the installer (encoding all of an existing program's files in one pass), use a one-off helper script. Example:

```python
#!/usr/bin/env python3
"""
encode_program.py — Walk a source tree and emit FILES + HASHES dict literals
for pasting into install.py.
"""
import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP_DIRS  = {'.git', '__pycache__', 'logs', 'reports', 'secrets', '.venv', 'venv'}
SKIP_FILES = {'install.py', 'encode_program.py'}
PROTECTED  = {
    'secrets/sync_keys.json',
    'config/tokens/token_nicktat.json',
    'config/google_creds/credentials_nicktat.json',
    'config/blaze_configs/blaze_config_nicktat.json',
    'PROGRAM_CREDENTIALS.json',
}

def walk(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rel = p.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in p.parts): continue
        if p.name in SKIP_FILES: continue
        if rel in PROTECTED: continue
        out.append(p)
    return sorted(out)

def main() -> None:
    files: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for p in walk(ROOT):
        rel = p.relative_to(ROOT).as_posix()
        b = p.read_bytes()
        files[rel]  = base64.b64encode(b).decode('ascii')
        hashes[rel] = hashlib.sha256(b).hexdigest()
        print(f"  + {rel}  ({len(b):>8} bytes)")
    # Emit FILES dict
    print("\n\nFILES: dict[str, str] = {")
    for k, v in files.items():
        print(f"    {k!r:50}: {v!r},")
    print("}\n")
    print("HASHES: dict[str, str] = {")
    for k, v in hashes.items():
        print(f"    {k!r:50}: {v!r},")
    print("}")

if __name__ == "__main__":
    main()
```

Pipe the output to a file, paste into the installer skeleton, done. This is a one-shot bootstrap helper — after the installer exists, all edits go through the agent workflow (§7).

A companion helper script (`gather_for_claude.py` in the reference implementation) safely copies all tracked source files into a `FOR_CLAUDE/` folder for chat upload, so the AI agent can see the actual current state when needed.

---

## 10. Self-healing behavior — what makes this a "healing" installer

Every time the user runs `python install.py`, the installer:

1. **Re-creates any missing directories** (mkdir is idempotent — already-existing dirs are no-ops).
2. **Re-writes any new files** (paths in `FILES` that don't exist on disk).
3. **Re-writes any drifted files** (paths whose disk hash != expected hash). If a virus scanner truncates a file, if the user accidentally edits one, if a disk write was interrupted — the installer detects it and restores from the embedded copy.
4. **Re-installs any missing pip packages** (pip is idempotent — already-installed packages are no-ops).
5. **Re-creates any missing credential placeholders** (but never overwrites existing credentials).
6. **Reports exactly what it did** with the colored Unchanged / New / Updated summary.

This is the **"healing"** part of "self install, setup, healing/updating". The installer is **idempotent under the assumption that the user has not externally modified the embedded `FILES`/`HASHES` dicts**. Running it twice in a row produces the same end state. Running it after a partial corruption recovers to the embedded state. Running it after an upstream update writes only the diff.

---

## 11. Version naming convention

`SCRIPT_VERSION` strings follow the format:

```
YYYY-MM-DD-DESCRIPTOR-VN
```

Examples from the reference implementation:
- `"2026-04-17-MONTHLY-FIX-V11"`
- `"2026-04-21-MASS-EDIT-RENAME-V12"`
- `"2026-04-25-BLAZE-LOGIN-CASCADE-V18.1"`
- `"2026-05-07-ZOMBIE-CLEANUP-RESTORE-V26.1"`

**Rules:**
- Date is the date of the change (not the date the change was first conceived).
- `DESCRIPTOR` is uppercase, hyphen-separated, briefly identifies the change.
- `VN` is the sequential version number. Use sub-versions (e.g. `V18.1`) for hot-fix follow-ups to a recent major change.
- The version string is printed on every install run, so the user can verify they're running the build they expect.

---

## 12. Where to display version, and what for

The installer prints `SCRIPT_VERSION` at the top of its run banner:

```
  PROGRAM_NAME installer  ·  2026-05-26-INITIAL-V1
  ============================================================
```

The program itself should also expose `SCRIPT_VERSION` somewhere visible at runtime — typically:
- `/health` endpoint JSON response: `{"version": "...", ...}`
- The HTML page footer
- The console log on app startup

This lets the user verify that the on-disk codebase matches the installer they last ran. If `/health` shows an older version than the installer they just ran, something is wrong (probably they re-ran an old installer by accident).

To wire this up, embed `SCRIPT_VERSION` as a string constant in one of the program's source files (e.g. `src/app.py::APP_VERSION`) and update both the installer's `SCRIPT_VERSION` and the source file's `APP_VERSION` in the same edit. The source file's value will be base64-re-encoded and re-hashed as part of the same change.

---

## 13. Color output — the user-visible polish

The installer is a CLI tool the user watches scroll by. Use ANSI color codes to make the output scannable:

| Helper | Color | Symbol | Use for |
|---|---|---|---|
| `_ok(msg)`   | green  (`\033[32m`) | `✓` | Success: "Python 3.10 OK", "wrote X" |
| `_warn(msg)` | yellow (`\033[33m`) | `⚠` | Non-fatal: "missing critical file", "placeholder needs filling" |
| `_err(msg)`  | red    (`\033[31m`) | `✗` | Fatal: "Python too old", pip errors |
| `_dim(msg)`  | grey   (`\033[90m`) | (none) | Sub-detail under a header: file names in diff lists |

Each helper does its own `print()`. Always end with `\033[0m` reset so the terminal doesn't bleed color into subsequent output.

The visual rhythm matters: the user knows the installer is healthy when they see a wall of green ✓s. They know something is wrong when they see yellow or red. Don't dilute this signal by using `_ok` for routine info — reserve it for genuine successes.

---

## 14. Logging — hybrid console + file pattern

Per project rule #5 ("Hybrid logging rule"), all programs Nick builds use a hybrid pattern: `print()` for live console feedback during headless operations + the `logging` module for persistent file output. Never one without the other.

**Inside the installer:** `print()` only is acceptable, since the installer is short-lived and the user is watching it run. But the program itself (the embedded files) must follow the full hybrid pattern in its own `src/utils/logger.py` or equivalent.

A canonical hybrid-logging helper:

```python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent   # NEVER Path.cwd()
_LOG_DIR = _PROJECT_ROOT / 'logs'
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_handler = RotatingFileHandler(
    _LOG_DIR / 'app.log',
    maxBytes=5 * 1024 * 1024,   # 5 MB per file
    backupCount=3,              # Keep 3 backups
    encoding='utf-8',
)
_handler.setFormatter(logging.Formatter('%(asctime)s  %(levelname)-7s  %(name)s  %(message)s'))
logging.getLogger().addHandler(_handler)
logging.getLogger().setLevel(logging.INFO)

def console_log(message: str, level: str = 'info', logger_name: str = 'app') -> None:
    """Hybrid log: print for live console + logging for file persistence."""
    print(message)
    log = logging.getLogger(logger_name)
    getattr(log, level.lower(), log.info)(message)
```

Then throughout the program: `from src.utils.logger import console_log` and use it instead of bare `print`.

---

## 15. Critical do's and don'ts — final summary

### DO
- ✅ Use one file for the whole codebase.
- ✅ Encode every source file as base64, one entry per line.
- ✅ Hash every decoded file's bytes with SHA-256.
- ✅ Use `detect_mode()` to branch between install and update — same code path otherwise.
- ✅ Protect credential files via the `PROTECTED` set.
- ✅ Anchor all paths to `Path(__file__).resolve().parent`.
- ✅ Require Python 3.10+ for `dict[str, str]` syntax and type hints.
- ✅ Bump `SCRIPT_VERSION` on every change.
- ✅ Print colored ✓ / ⚠ / ✗ so the user can scan the output.
- ✅ Validate Python syntax (`ast.parse`) before delivering the installer.
- ✅ Roundtrip-verify (decode → hash → compare) before delivering the installer.
- ✅ Make every step idempotent (re-runs leave the system in the same state).

### DON'T
- ❌ Don't put credentials in `FILES`. Use the unified-credentials split pattern.
- ❌ Don't use `Path.cwd()`. Use `Path(__file__).resolve().parent`.
- ❌ Don't use `os.path.join`. Use `pathlib.Path` (project rule #3).
- ❌ Don't edit `FILES` without also editing `HASHES`.
- ❌ Don't rewrite the installer from scratch. Use `str_replace`.
- ❌ Don't overwrite existing credential files. Always guard with `if dest.exists(): continue`.
- ❌ Don't forget to bump `SCRIPT_VERSION`.
- ❌ Don't trust the user's machine to have a specific Python version — check it in step 1 and exit gracefully if too old.
- ❌ Don't trust the user's directory layout — `mkdir(parents=True, exist_ok=True)` everywhere.
- ❌ Don't write a thousand bullet points about every edge case in the docstring. Keep the installer tight (~250–300 lines including the dicts).

---

## 16. Recommended directory layout for a new program

For consistency with Nick's existing programs:

```
PROGRAM_ROOT/
├── install.py                  # ← THE FILE the agent edits
├── Launcher.py                 # boot wrapper (env injection, dep check, Chrome launch, run.py spawn)
├── run.py                      # Flask entry point — calls create_app()
├── settings.json               # user-facing settings (copied to config/settings.json)
├── encode_program.py           # one-off bootstrap helper for initial encoding
├── gather_for_claude.py        # helper to copy current source files into FOR_CLAUDE/
├── src/
│   ├── __init__.py             # blank
│   ├── app.py                  # Flask app factory (sentinel for detect_mode)
│   ├── session/
│   │   ├── __init__.py         # special-case from SESSION_INIT_CONTENT
│   │   ├── manager.py          # SessionManager singleton
│   │   └── storage_backends.py
│   ├── api/                    # Flask blueprints
│   │   └── __init__.py
│   ├── core/                   # business logic
│   │   └── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py           # hybrid logger
│   └── integrations/           # external services
│       └── __init__.py
├── static/
│   ├── js/
│   └── css/
├── templates/
│   └── index.html
├── config/
│   ├── tokens/
│   ├── google_creds/
│   ├── blaze_configs/
│   └── chrome/
├── secrets/                    # PROTECTED — never embedded
├── reports/
└── logs/
```

The installer's `DIRS` constant should list every directory in this tree (so they're all created on first run).

---

## 17. Acceptance checklist for the next AI agent

Before delivering the first version of the new installer, verify:

- [ ] One file contains the entire program.
- [ ] `FILES` dict has every source file as base64.
- [ ] `HASHES` dict has matching SHA-256 of decoded bytes for every entry in `FILES`.
- [ ] `DIRS` lists every directory in the tree.
- [ ] `BLANK_INITS` lists every `__init__.py` that should be empty.
- [ ] `PACKAGES` lists every pip dep with `>=` version pins.
- [ ] `PROTECTED` lists every credential file path.
- [ ] `SESSION_INIT_CONTENT` is a plain-text literal (not in `FILES`).
- [ ] `SCRIPT_VERSION` follows the `YYYY-MM-DD-DESCRIPTOR-VN` format.
- [ ] `HERE = Path(__file__).resolve().parent` is set in the header.
- [ ] All paths use `pathlib.Path`, none use `os.path.join`.
- [ ] All function signatures use Python 3.10+ type hints.
- [ ] `main()` has all 6 steps in the order specified.
- [ ] `detect_mode()` returns 'install' or 'update' based on a sentinel file.
- [ ] `scan_files()` returns `(nf, cf, uf)` tuple and skips `PROTECTED`.
- [ ] `write_files()` skips `PROTECTED` and special-cases the session `__init__.py`.
- [ ] Step 4 (credentials) implements the unified-split → legacy-copy → placeholder fallback chain.
- [ ] Step 5 (smoke check) lists every critical boot file.
- [ ] Step 6 (pip) uses `subprocess.run` with `capture_output=True`.
- [ ] Color helpers `_ok` / `_warn` / `_err` / `_dim` are defined.
- [ ] Final prompt offers to launch the program with `y/N`.
- [ ] Python syntax validates via `ast.parse`.
- [ ] Roundtrip verification: every `FILES[k]` decodes to bytes whose SHA-256 == `HASHES[k]`.
- [ ] Installer runs cleanly on a fresh directory (install mode).
- [ ] Installer runs cleanly when re-run (update mode, all unchanged).
- [ ] Installer runs cleanly when one file is manually corrupted (update mode, restores it).

If every box is checked, deliver. Otherwise, fix and re-verify.

---

## 18. Where this document fits in the broader workflow

This document is **descriptive**, not prescriptive about content. Apply the pattern to whatever new program Nick wants to build. The specific lists of `DIRS`, `PACKAGES`, `PROTECTED`, etc. will differ from the reference implementation — that's expected.

What does NOT differ:
- The 5-region file layout.
- The base64 + SHA-256 encoding scheme.
- The 6-step `main()` workflow.
- The unified-credentials split + per-file fallback + placeholder chain.
- The agent edit workflow (decode → edit → re-encode → re-hash → str_replace → bump version → validate → roundtrip).
- The anti-patterns list.

If a future agent asks "should I deviate from this pattern for my use case?" — the answer is almost always no. The pattern is the result of dozens of iterations of debugging real production issues (regressions, drift, credential leaks, partial updates). Deviation has cost; conformance has none.

---

**End of handoff document.**

> Last updated: 2026-05-26. Reference implementation: Blaze MIS Audit Pro `install8.py`, `SCRIPT_VERSION = "2026-05-07-ZOMBIE-CLEANUP-RESTORE-V26.1"`, 48 tracked files, ~272 lines.
