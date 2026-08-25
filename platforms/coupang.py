from platforms.base_platform import BasePlatform


class CoupangPlatform(BasePlatform):
    name = "쿠팡이츠"
    login_url = "https://store.coupangeats.com/"
    reviews_url = "https://store.coupangeats.com/"
    unanswered_filter_sel = "text=미답변"

    def ready(self) -> bool:
        return bool(self.user and self.password)
