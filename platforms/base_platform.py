from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout


@dataclass
class ReviewItem:
    text: str
    star: int | None = None
    menu: str = ""
    already_replied: bool = False
    card_index: int = 0


class BasePlatform(ABC):
    name = "platform"
    login_url = ""
    reviews_url = ""
    user_sel = 'input[type="text"], input[name="id"], input[name="username"], input[type="email"]'
    pass_sel = 'input[type="password"]'
    login_btn_sel = 'button[type="submit"]'
    unanswered_filter_sel = 'text=미답변'
    review_card_sel = '[class*="review"], [class*="Review"], li, article'
    reply_box_sel = "textarea"
    submit_sel = 'button:has-text("등록"), button:has-text("작성"), button:has-text("답글")'

    def __init__(self, page: Page, user: str, password: str, type_delay_ms: int, manual_auth_wait_sec: int):
        self.page = page
        self.user = user
        self.password = password
        self.type_delay_ms = type_delay_ms
        self.manual_auth_wait_sec = manual_auth_wait_sec

    def human_pause(self, lo: float = 0.25, hi: float = 0.7) -> None:
        time.sleep(random.uniform(lo, hi))

    def type_human(self, selector: str, value: str) -> None:
        loc = self.page.locator(selector).first
        loc.wait_for(state="visible", timeout=20000)
        loc.click()
        loc.fill("")
        loc.type(value, delay=self.type_delay_ms)

    def wait_after_login(self) -> None:
        """SMS/OTP/캡차가 있으면 headful 화면에서 직접 완료할 시간을 줍니다."""
        self.page.wait_for_timeout(min(self.manual_auth_wait_sec, 8) * 1000)

    def login(self) -> None:
        if not self.user or not self.password:
            raise RuntimeError(f"{self.name}: .env 에 아이디/비밀번호가 없습니다.")
        self.page.goto(self.login_url, wait_until="domcontentloaded")
        self.page.wait_for_selector(self.user_sel, timeout=25000)
        self.type_human(self.user_sel, self.user)
        self.human_pause()
        self.type_human(self.pass_sel, self.password)
        self.human_pause(0.4, 0.9)
        try:
            self.page.locator(self.login_btn_sel).first.click()
        except PlaywrightTimeout:
            self.page.keyboard.press("Enter")
        self.wait_after_login()

    def open_reviews(self) -> None:
        if self.reviews_url:
            self.page.goto(self.reviews_url, wait_until="domcontentloaded")
        self.human_pause(0.6, 1.2)
        try:
            self.page.locator(self.unanswered_filter_sel).first.click(timeout=5000)
            self.human_pause(0.5, 1.0)
        except PlaywrightTimeout:
            pass

    def looks_replied(self, card) -> bool:
        blob = (card.inner_text() or "")
        markers = ("사장님 댓글", "사장님 답글", "답글 완료", "답변이 등록", "수정하기")
        return any(m in blob for m in markers)

    def parse_star(self, card) -> int | None:
        blob = card.inner_text() or ""
        for n in range(5, 0, -1):
            if f"{n}점" in blob or f"별점 {n}" in blob or ("★" * n) in blob:
                return n
        return None

    def parse_menu(self, card) -> str:
        blob = card.inner_text() or ""
        for line in blob.splitlines():
            line = line.strip()
            if "메뉴" in line or "주문" in line:
                return line[:80]
        return ""

    def collect_unanswered(self, limit: int) -> list[ReviewItem]:
        self.page.wait_for_selector(self.review_card_sel, timeout=20000)
        cards = self.page.locator(self.review_card_sel)
        items: list[ReviewItem] = []
        count = min(cards.count(), 80)
        for i in range(count):
            if len(items) >= limit:
                break
            card = cards.nth(i)
            text = (card.inner_text() or "").strip()
            if len(text) < 8:
                continue
            if self.looks_replied(card):
                continue
            items.append(
                ReviewItem(
                    text=text[:1500],
                    star=self.parse_star(card),
                    menu=self.parse_menu(card),
                    already_replied=False,
                    card_index=i,
                )
            )
        return items

    def write_reply_on_card(self, index: int, reply: str) -> None:
        card = self.page.locator(self.review_card_sel).nth(index)
        box = card.locator(self.reply_box_sel).first
        try:
            box.wait_for(state="visible", timeout=4000)
        except PlaywrightTimeout:
            card.click()
            self.human_pause()
            box = self.page.locator(self.reply_box_sel).first
            box.wait_for(state="visible", timeout=8000)
        box.click()
        box.fill("")
        box.type(reply, delay=self.type_delay_ms)
        self.human_pause(0.3, 0.8)
        submit = card.locator(self.submit_sel).first
        if submit.count() == 0:
            submit = self.page.locator(self.submit_sel).first
        submit.click()
        self.human_pause(0.8, 1.4)

    def run(self, generate_fn, max_replies: int, log=print) -> int:
        done = 0
        self.login()
        self.open_reviews()
        reviews = self.collect_unanswered(max_replies)
        log(f"[{self.name}] 미답변 리뷰 {len(reviews)}건 감지")
        for item in reviews:
            if item.already_replied:
                continue
            reply = generate_fn(item.text, item.star, item.menu)
            try:
                self.write_reply_on_card(item.card_index, reply)
                done += 1
                log(f"[{self.name}] AI 답글 등록 완료 ({done}/{len(reviews)})")
            except Exception as exc:
                log(f"[{self.name}] 등록 실패: {exc}")
                continue
        return done

    @abstractmethod
    def ready(self) -> bool:
        ...
