from platforms.base_platform import BasePlatform


class DdangyoPlatform(BasePlatform):
    name = "땡겨요"
    login_url = "https://boss.ddangyo.com/"
    reviews_url = "https://boss.ddangyo.com/"
    unanswered_filter_sel = "text=미답변"

    def ready(self) -> bool:
        return bool(self.user and self.password)
