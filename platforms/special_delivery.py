from platforms.base_platform import BasePlatform


class SpecialDeliveryPlatform(BasePlatform):
    name = "배달특급"
    login_url = "https://partner.payco.kr/"
    reviews_url = "https://partner.payco.kr/"
    unanswered_filter_sel = "text=미답변"

    def ready(self) -> bool:
        return bool(self.user and self.password)
