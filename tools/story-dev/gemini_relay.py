"""Gemini API relay — lets the agent ask Gemini research questions directly
(user directive 2026-07-23: the automation path from 15-ESCALATION-RESEARCH.md).

Usage:
    py gemini_relay.py "your question"                  # one-shot prompt
    py gemini_relay.py --file prompt.md                 # prompt from a file
    py gemini_relay.py --file primer.md --file q.md     # multiple parts, in order
    py gemini_relay.py --model gemini-2.5-pro "..."     # model override
    py gemini_relay.py --list-models                    # discover available models
    py gemini_relay.py --out answer.md "..."            # also write the answer to a file

Key resolution: $GEMINI_API_KEY env var, else `sandbox-pokebot/profiles/gemini.key`
(gitignored — NEVER commit the key; the standing no-secrets rule applies).

House rules baked into how this is used, not the tool: answers are LEADS — every
flag/var/coord goes through audit_flag_names.py / decomp checks, and every
learnset/TM claim through modules/data, before any code is written.
"""

import argparse
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_KEY_FILE = _ROOT / "sandbox-pokebot" / "profiles" / "gemini.key"
_BASE = "https://generativelanguage.googleapis.com/v1beta"
# User directive 2026-07-23: consults default to Gemini 3.1 Pro for better results.
# Use --model gemini-2.5-flash (or 3.1-flash-lite) for cheap factual one-liners.
DEFAULT_MODEL = "gemini-3.1-pro-preview"


def _key() -> str:
    import os

    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k and _KEY_FILE.exists():
        k = _KEY_FILE.read_text(encoding="utf-8").strip()
    if not k:
        sys.exit("No API key: set GEMINI_API_KEY or create sandbox-pokebot/profiles/gemini.key")
    return k


def _request(url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "x-goog-api-key": _key()},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"HTTP {e.code} from Gemini API:\n{body[:2000]}")


def list_models() -> None:
    data = _request(f"{_BASE}/models")
    for m in data.get("models", []):
        methods = ",".join(m.get("supportedGenerationMethods", []))
        if "generateContent" in methods:
            print(f"  {m['name'].removeprefix('models/')}   ({m.get('displayName', '')})")


def ask(parts: list[str], model: str, retries: int = 3) -> str:
    payload = {
        "contents": [{"role": "user", "parts": [{"text": p} for p in parts]}],
    }
    for attempt in range(retries):
        data = _request(f"{_BASE}/models/{model}:generateContent", payload)
        try:
            candidates = data["candidates"]
            out = "".join(
                p.get("text", "") for p in candidates[0]["content"]["parts"]
            )
            if out.strip():
                return out
        except (KeyError, IndexError):
            pass
        # Empty/blocked response — brief backoff then retry.
        if attempt < retries - 1:
            time.sleep(5 * (attempt + 1))
    sys.exit(f"Gemini returned no usable text after {retries} attempts:\n{json.dumps(data)[:2000]}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Relay a research prompt to the Gemini API.")
    ap.add_argument("prompt", nargs="*", help="prompt text (joined with spaces)")
    ap.add_argument("--file", action="append", default=[], help="read prompt part(s) from file(s), in order")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out", help="also write the answer to this file")
    ap.add_argument("--list-models", action="store_true")
    args = ap.parse_args()

    if args.list_models:
        list_models()
        return

    parts = [pathlib.Path(f).read_text(encoding="utf-8") for f in args.file]
    if args.prompt:
        parts.append(" ".join(args.prompt))
    if not parts:
        ap.error("no prompt given (positional text or --file)")

    answer = ask(parts, args.model)
    # ‼ WRITE THE FILE FIRST, AND NEVER LET PRINTING LOSE THE ANSWER (2026-07-24).
    # Two of ten research calls were destroyed by `print(answer)` raising
    # UnicodeEncodeError: the Windows console is cp1252 and Gemini answers routinely
    # contain '→' / '↓'. Because the print came BEFORE the write, the crash threw away a
    # complete, already-paid-for API response. So: persist first, then print defensively.
    if args.out:
        pathlib.Path(args.out).write_text(answer, encoding="utf-8")
    try:
        print(answer)
    except UnicodeEncodeError:
        # Console can't represent it; the file (if any) already has the real text.
        sys.stdout.buffer.write(answer.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")
    if args.out:
        print(f"\n[written to {args.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
