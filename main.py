import traceback
from typing import Callable

from playwright.sync_api import sync_playwright

import config
from gemini_service import generate_reply
from platforms.baemin import BaeminPlatform
from platforms.coupang import CoupangPlatform
from platforms.ddangyo import DdangyoPlatform
from platforms.special_delivery import SpecialDeliveryPlatform
from platforms.yogiyo import YogiyoPlatform

BUILDERS = [
    ("baemin", BaeminPlatform),
    ("coupang", CoupangPlatform),
    ("yogiyo", YogiyoPlatform),
    ("ddangyo", DdangyoPlatform),
    ("special", SpecialDeliveryPlatform),
]


def log(msg: str) -> None:
    print(msg, flush=True)


def run_all(logger: Callable[[str], None] | None = None) -> list[tuple[str, int | str]]:
    emit = logger or log
    config.reload()
    if not config.GEMINI_API_KEY:
        emit("GEMINI_API_KEY 가 없습니다. 대시보드에서 API 키를 저장하세요.")
        return [("설정", "missing api key")]

    summary: list[tuple[str, int | str]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not config.HEADFUL,
            slow_mo=config.SLOW_MO_MS,
        )
        context = browser.new_context(locale="ko-KR")
        page = context.new_page()

        for key, cls in BUILDERS:
            if not config.ENABLED.get(key, True):
                emit(f"[건너뜀] {cls.name}: 비활성화")
                summary.append((cls.name, "off"))
                continue
            user, pw = config.CREDENTIALS[key]
            bot = cls(
                page,
                user,
                pw,
                type_delay_ms=config.TYPE_DELAY_MS,
                manual_auth_wait_sec=config.MANUAL_AUTH_WAIT_SEC,
            )
            if not bot.ready():
                emit(f"[건너뜀] {bot.name}: 계정 정보가 없습니다.")
                summary.append((bot.name, "skipped"))
                continue
            try:
                emit(f"[시작] {bot.name}")
                count = bot.run(generate_reply, config.MAX_REPLIES_PER_PLATFORM, log=emit)
                emit(f"[완료] {bot.name} {count}건 완료")
                summary.append((bot.name, count))
            except Exception as exc:
                emit(f"[실패] {bot.name}: {exc}")
                traceback.print_exc()
                summary.append((bot.name, f"error: {exc}"))

        context.close()
        browser.close()

    emit("===== 요약 =====")
    for name, result in summary:
        emit(f"- {name}: {result}")
    return summary


def test_login(platform_key: str, logger: Callable[[str], None] | None = None) -> bool:
    emit = logger or log
    config.reload()
    mapping = dict(BUILDERS)
    cls = mapping.get(platform_key)
    if not cls:
        emit("알 수 없는 플랫폼입니다.")
        return False
    user, pw = config.CREDENTIALS.get(platform_key, ("", ""))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=config.SLOW_MO_MS)
        page = browser.new_context(locale="ko-KR").new_page()
        bot = cls(page, user, pw, config.TYPE_DELAY_MS, config.MANUAL_AUTH_WAIT_SEC)
        try:
            emit(f"[{bot.name}] 로그인 테스트 시작 (OTP가 있으면 화면에서 완료하세요)")
            bot.login()
            emit(f"[{bot.name}] 로그인 단계 완료")
            return True
        except Exception as exc:
            emit(f"[{bot.name}] 로그인 테스트 실패: {exc}")
            return False
        finally:
            browser.close()


def main() -> None:
    run_all()


if __name__ == "__main__":
    main()
