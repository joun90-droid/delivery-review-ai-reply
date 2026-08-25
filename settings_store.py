from __future__ import annotations

import json
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT / ".secrets.key"
STORE_PATH = ROOT / ".settings.enc"

DEFAULTS = {
    "gemini_api_key": "",
    "reply_tone": "polite",
    "store_guide": "",
    "headful": True,
    "platforms": {
        "baemin": {"enabled": True, "id": "", "pw": ""},
        "coupang": {"enabled": True, "id": "", "pw": ""},
        "yogiyo": {"enabled": True, "id": "", "pw": ""},
        "ddangyo": {"enabled": True, "id": "", "pw": ""},
        "special": {"enabled": True, "id": "", "pw": ""},
    },
}


def _fernet() -> Fernet:
    if KEY_PATH.exists():
        key = KEY_PATH.read_bytes().strip()
    else:
        key = Fernet.generate_key()
        KEY_PATH.write_bytes(key)
        try:
            KEY_PATH.chmod(0o600)
        except OSError:
            pass
    return Fernet(key)


def load_settings() -> dict:
    data = json.loads(json.dumps(DEFAULTS))
    if not STORE_PATH.exists():
        return data
    try:
        raw = _fernet().decrypt(STORE_PATH.read_bytes())
        saved = json.loads(raw.decode("utf-8"))
    except (InvalidToken, ValueError, json.JSONDecodeError):
        return data
    data.update({k: saved[k] for k in ("gemini_api_key", "reply_tone", "store_guide", "headful") if k in saved})
    for key, plat in data["platforms"].items():
        incoming = (saved.get("platforms") or {}).get(key) or {}
        plat.update({k: incoming[k] for k in incoming if k in plat})
    return data


def save_settings(data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    STORE_PATH.write_bytes(_fernet().encrypt(payload))
