import traceback

from playwright.sync_api import sync_playwright

import config
from gemini_service import generate_reply
from platforms.baemin import BaeminPlatform
from platforms.coupang import CoupangPlatform
from platforms.ddangyo import DdangyoPlatform
from platforms.special_delivery import SpecialDeliveryPlatform
from platforms.yogiyo import YogiyoPlatform


def log(msg: str) -> None:
    print(msg, flush=True)


def main() -> None:
    if not config.GEMINI_API_KEY:
        log("GEMINI_API_KEY 가 없습니다. .env.example 을 복사해 .env 를 만드세요.")
        return

    builders = [
        ("baemin", BaeminPlatform),
        ("coupang", CoupangPlatform),
        ("yogiyo", YogiyoPlatform),
        ("ddangyo", DdangyoPlatform),
        ("special", SpecialDeliveryPlatform),
    ]
    summary: list[tuple[str, int | str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not config.HEADFUL,
            slow_mo=config.SLOW_MO_MS,
        )
        context = browser.new_context(locale="ko-KR")
        page = context.new_page()

        for key, cls in builders:
            user, pw = config.CREDENTIALS[key]
            bot = cls(
                page,
                user,
                pw,
                type_delay_ms=config.TYPE_DELAY_MS,
                manual_auth_wait_sec=config.MANUAL_AUTH_WAIT_SEC,
            )
            if not bot.ready():
                log(f"[건너뜀] {bot.name}: 계정 정보가 없습니다.")
                summary.append((bot.name, "skipped"))
                continue
            try:
                log(f"[시작] {bot.name}")
                count = bot.run(generate_reply, config.MAX_REPLIES_PER_PLATFORM)
                log(f"[완료] {bot.name} {count}건 완료")
                summary.append((bot.name, count))
            except Exception as exc:
                log(f"[실패] {bot.name}: {exc}")
                traceback.print_exc()
                summary.append((bot.name, f"error: {exc}"))

        context.close()
        browser.close()

    log("\n===== 요약 =====")
    for name, result in summary:
        log(f"- {name}: {result}")


if __name__ == "__main__":
    main()
