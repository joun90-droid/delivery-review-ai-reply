from platforms.base_platform import BasePlatform


class YogiyoPlatform(BasePlatform):
    name = "요기요"
    login_url = "https://partner.yogiyo.co.kr/"
    reviews_url = "https://partner.yogiyo.co.kr/"
    unanswered_filter_sel = "text=미답변"

    def ready(self) -> bool:
        return bool(self.user and self.password)
