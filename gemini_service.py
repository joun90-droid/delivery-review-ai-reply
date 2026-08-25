import google.generativeai as genai

import config


def _strategy(star: int | None, review: str) -> str:
    text = review or ""
    if star is not None and star <= 2:
        return (
            "1~2점 불만. 진심 어린 사과, 개선 약속, 매장으로 연락 달라는 멘트를 넣는다. "
            "재주문 강요는 하지 않는다."
        )
    if star is not None and star >= 5:
        return "5점 칭찬. 감사 인사와 재주문·단골 유도 멘트를 자연스럽게 넣는다."
    if any(w in text for w in ("별로", "최악", "실망", "늦", "식었", "누락", "맛없")):
        return "불만 키워드. 사과와 개선 약속 위주."
    return "감사와 정성스러운 안내. 과한 재주문 유도는 피한다."


def generate_reply(review_text: str, star_rating: int | None = None, menu_name: str = "") -> str:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY 가 .env 에 없습니다.")

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    star_line = f"{star_rating}점" if star_rating else "미확인"
    menu_line = menu_name.strip() or "미확인"
    prompt = f"""너는 한국 배달 음식점 사장님이다. 답글 본문만 출력한다.

[톤앤매너] {config.tone_instruction()}
[매장 지침] {config.STORE_GUIDE}
[별점] {star_line}
[주문 메뉴] {menu_line}
[작성 전략] {_strategy(star_rating, review_text)}
[고객 리뷰]
\"\"\"{review_text.strip()}\"\"\"

규칙:
- 3줄 내외, 자연스럽고 정성스러운 사장님 어투.
- 리뷰에 나온 메뉴나 이슈를 한 가지 이상 언급.
- 마크다운·따옴표·제목 없이 답글만."""

    result = model.generate_content(prompt)
    text = (getattr(result, "text", None) or "").strip()
    if not text:
        raise RuntimeError("Gemini 가 빈 답글을 반환했습니다.")
    return text
