import os
from dotenv import load_dotenv

from settings_store import load_settings

load_dotenv()

TONE_PROMPTS = {
    "kind": "친절하고 감성적. 따뜻한 공감, 다정한 사장님 말투.",
    "polite": "정중하고 깔끔. 담백한 사장님 말투. 과도한 이모지 금지.",
    "firm": "악플·오해에 단호히 대처. 욕설 맞대응 금지. 사실과 사과, 개선을 차분하게.",
    "short": "반드시 한 문장만. 인사와 핵심만.",
}


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


SLOW_MO_MS = _int("SLOW_MO_MS", 80)
TYPE_DELAY_MS = _int("TYPE_DELAY_MS", 90)
MAX_REPLIES_PER_PLATFORM = _int("MAX_REPLIES_PER_PLATFORM", 10)
MANUAL_AUTH_WAIT_SEC = _int("MANUAL_AUTH_WAIT_SEC", 120)

GEMINI_API_KEY = ""
REPLY_TONE = "polite"
STORE_GUIDE = ""
HEADFUL = True
CREDENTIALS = {}
ENABLED = {}


def reload() -> None:
    global GEMINI_API_KEY, REPLY_TONE, STORE_GUIDE, HEADFUL, CREDENTIALS, ENABLED
    saved = load_settings()
    GEMINI_API_KEY = (saved.get("gemini_api_key") or os.getenv("GEMINI_API_KEY", "")).strip()
    REPLY_TONE = (saved.get("reply_tone") or os.getenv("REPLY_TONE", "polite")).strip() or "polite"
    STORE_GUIDE = (saved.get("store_guide") or os.getenv("STORE_GUIDE", "배달 음식점 사장님")).strip()
    if "headful" in saved:
        HEADFUL = bool(saved["headful"])
    else:
        HEADFUL = _env_bool("HEADFUL", True)

    env_map = {
        "baemin": ("BAEMIN_ID", "BAEMIN_PW"),
        "coupang": ("COUPANG_ID", "COUPANG_PW"),
        "yogiyo": ("YOGIYO_ID", "YOGIYO_PW"),
        "ddangyo": ("DDANGYO_ID", "DDANGYO_PW"),
        "special": ("SPECIAL_ID", "SPECIAL_PW"),
    }
    CREDENTIALS = {}
    ENABLED = {}
    plats = saved.get("platforms") or {}
    for key, (id_k, pw_k) in env_map.items():
        row = plats.get(key) or {}
        uid = (row.get("id") or os.getenv(id_k, "")).strip()
        pw = (row.get("pw") or os.getenv(pw_k, "")).strip()
        CREDENTIALS[key] = (uid, pw)
        ENABLED[key] = bool(row.get("enabled", True)) if key in plats else True


def tone_instruction() -> str:
    return TONE_PROMPTS.get(REPLY_TONE, TONE_PROMPTS["polite"])


reload()
