from __future__ import annotations

import os
from pathlib import Path

import win32clipboard
import win32crypt


def main() -> int:
    win32clipboard.OpenClipboard()
    try:
        value = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()

    if not isinstance(value, str):
        print("BLOCKED: clipboard does not contain text")
        return 20

    secret = value.strip()
    if len(secret) < 20 or any(ch.isspace() for ch in secret):
        print("BLOCKED: clipboard text does not look like an API key")
        return 21

    root = Path(os.environ["LOCALAPPDATA"]) / "ZNAK" / "secrets"
    root.mkdir(parents=True, exist_ok=True)
    target = root / "nebius_api_key.dpapi"

    _, encrypted = win32crypt.CryptProtectData(
        secret.encode("utf-8"),
        "ZNAK Nebius Token Factory API key",
        None,
        None,
        None,
        0,
    )
    target.write_bytes(encrypted)

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
    finally:
        win32clipboard.CloseClipboard()

    print("KEY_STORED_DPAPI=True")
    print("CLIPBOARD_CLEARED=True")
    print("SECRET_PRINTED=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
