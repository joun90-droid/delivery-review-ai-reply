import os
from dotenv import load_dotenv

load_dotenv()

TONE_PROMPTS = {
    "kind": "친절하고 감성적. 따뜻한 공감, 다정한 사장님 말투.",
    "polite": "정중하고 깔끔. 담백한 사장님 말투. 과도한 이모지 금지.",
    "firm": "악플·오해에 단호히 대처. 욕설 맞대응 금지. 사실과 사과, 개선을 차분하게.",
    "short": "반드시 한 문장만. 인사와 핵심만.",
}


def _bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
REPLY_TONE = os.getenv("REPLY_TONE", "polite").strip() or "polite"
STORE_GUIDE = os.getenv("STORE_GUIDE", "배달 음식점 사장님").strip()
HEADFUL = _bool("HEADFUL", True)
SLOW_MO_MS = _int("SLOW_MO_MS", 80)
TYPE_DELAY_MS = _int("TYPE_DELAY_MS", 90)
MAX_REPLIES_PER_PLATFORM = _int("MAX_REPLIES_PER_PLATFORM", 10)
MANUAL_AUTH_WAIT_SEC = _int("MANUAL_AUTH_WAIT_SEC", 120)

CREDENTIALS = {
    "baemin": (os.getenv("BAEMIN_ID", "").strip(), os.getenv("BAEMIN_PW", "").strip()),
    "coupang": (os.getenv("COUPANG_ID", "").strip(), os.getenv("COUPANG_PW", "").strip()),
    "yogiyo": (os.getenv("YOGIYO_ID", "").strip(), os.getenv("YOGIYO_PW", "").strip()),
    "ddangyo": (os.getenv("DDANGYO_ID", "").strip(), os.getenv("DDANGYO_PW", "").strip()),
    "special": (os.getenv("SPECIAL_ID", "").strip(), os.getenv("SPECIAL_PW", "").strip()),
}


def tone_instruction() -> str:
    return TONE_PROMPTS.get(REPLY_TONE, TONE_PROMPTS["polite"])
