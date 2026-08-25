from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeout

from platforms.base_platform import BasePlatform, ReviewItem


class SpecialDeliveryPlatform(BasePlatform):
    name = "배달특급"
    login_url = "https://partner.payco.kr/"
    reviews_url = "https://partner.payco.kr/info/review/list"
    review_card_sel = "table tbody tr"
    unanswered_filter_sel = "text=미작성"
    submit_sel = 'button:has-text("등록"), button:has-text("저장"), button:has-text("작성"), button:has-text("답글")'

    def ready(self) -> bool:
        return bool(self.user and self.password)

    def _click_search(self) -> None:
        for name in ("조회", "검색"):
            btn = self.page.get_by_role("button", name=name)
            if btn.count():
                btn.first.click()
                self.human_pause(0.8, 1.4)
                return
        loc = self.page.locator("a, button, input[type='button']").filter(has_text="조회")
        if loc.count():
            loc.first.click()
            self.human_pause(0.8, 1.4)

    def _set_unanswered_filter(self) -> None:
        labels = ("미작성", "미답변", "답글 미작성", "미등록")
        selects = self.page.locator("select")
        count = selects.count()
        for i in range(count):
            sel = selects.nth(i)
            try:
                options = sel.locator("option")
                for j in range(options.count()):
                    text = (options.nth(j).inner_text() or "").strip()
                    if any(lab in text for lab in labels):
                        val = options.nth(j).get_attribute("value")
                        if val is not None:
                            sel.select_option(value=val)
                        else:
                            sel.select_option(index=j)
                        return
            except PlaywrightTimeout:
                continue
        for lab in labels:
            loc = self.page.get_by_text(lab, exact=False)
            if loc.count():
                loc.first.click()
                return

    def open_reviews(self) -> None:
        self.page.goto(self.reviews_url, wait_until="domcontentloaded")
        self.human_pause(0.8, 1.4)
        try:
            self.page.wait_for_selector("table", timeout=20000)
        except PlaywrightTimeout:
            pass
        self._set_unanswered_filter()
        self.human_pause(0.3, 0.6)
        self._click_search()
        self.page.wait_for_timeout(1200)

    def looks_replied(self, card) -> bool:
        blob = card.inner_text() or ""
        if "답글 작성 완료" in blob and "미작성" not in blob:
            return True
        return super().looks_replied(card)

    def parse_star(self, card) -> int | None:
        tds = card.locator("td")
        for i in range(tds.count()):
            t = (tds.nth(i).inner_text() or "").strip()
            if t in {"1", "2", "3", "4", "5"}:
                return int(t)
        return super().parse_star(card)

    def parse_menu(self, card) -> str:
        tds = card.locator("td")
        n = tds.count()
        if n >= 8:
            return (tds.nth(7).inner_text() or "").strip()[:80]
        return super().parse_menu(card)

    def collect_unanswered(self, limit: int) -> list[ReviewItem]:
        rows = self.page.locator("table tbody tr")
        try:
            rows.first.wait_for(timeout=15000)
        except PlaywrightTimeout:
            return []
        items: list[ReviewItem] = []
        total = min(rows.count(), 80)
        for i in range(total):
            if len(items) >= limit:
                break
            row = rows.nth(i)
            text = (row.inner_text() or "").strip()
            if len(text) < 8:
                continue
            if self.looks_replied(row):
                continue
            tds = row.locator("td")
            review = text
            if tds.count() >= 7:
                review = (tds.nth(6).inner_text() or text).strip()
            items.append(
                ReviewItem(
                    text=review[:1500],
                    star=self.parse_star(row),
                    menu=self.parse_menu(row),
                    already_replied=False,
                    card_index=i,
                )
            )
        return items

    def write_reply_on_card(self, index: int, reply: str) -> None:
        row = self.page.locator("table tbody tr").nth(index)
        tds = row.locator("td")
        if tds.count() >= 7:
            tds.nth(6).click()
        else:
            row.click()
        self.human_pause(0.6, 1.1)
        box = self.page.locator("textarea").last
        box.wait_for(state="visible", timeout=12000)
        box.click()
        box.fill("")
        box.type(reply, delay=self.type_delay_ms)
        self.human_pause(0.3, 0.8)
        clicked = False
        for name in ("등록", "저장", "작성", "확인"):
            btn = self.page.get_by_role("button", name=name)
            if btn.count():
                btn.last.click()
                clicked = True
                break
        if not clicked:
            self.page.locator(self.submit_sel).last.click()
        self.human_pause(0.9, 1.5)
