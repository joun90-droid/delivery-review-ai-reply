from platforms.base_platform import BasePlatform


class BaeminPlatform(BasePlatform):
    name = "배민"
    login_url = "https://ceo.baemin.com/"
    reviews_url = "https://ceo.baemin.com/"
    unanswered_filter_sel = "text=미답변"

    def ready(self) -> bool:
        return bool(self.user and self.password)
