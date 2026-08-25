const TONE_INSTRUCTIONS = {
  kind: '톤: 친절하고 감성적. 고객 마음을 따뜻하게 공감하고, 부드럽고 다정한 사장님 말투로 2~4줄 작성.',
  polite: '톤: 정중하고 깔끔. 군더더기 없이 담백한 사장님 말투로 2~3줄 작성. 과도한 이모지·감탄은 피함.',
  firm: '톤: 악플·비난에 단호히 대처. 욕설에 맞대응하지 말고, 사실·사과·개선 의지를 차분하고 단호하게 2~4줄로 작성. 감정 싸움은 금지.',
  short: '톤: 초간단. 반드시 한 문장(1줄)만 작성. 인사와 핵심만.'
};

const IDLE_LABEL = 'AI 답글 생성';
const ANALYZE_LABEL = 'AI가 리뷰 분석 중...';
const DONE_LABEL = '답글 작성 완료!';

function ensureButtonStyles() {
  if (document.getElementById('ai-reply-btn-styles')) return;
  const style = document.createElement('style');
  style.id = 'ai-reply-btn-styles';
  style.textContent = `
    .ai-reply-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin: 8px 0 10px;
      padding: 10px 16px;
      min-height: 40px;
      border: none;
      border-radius: 999px;
      color: #fff;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: -0.2px;
      font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Pretendard", sans-serif;
      cursor: pointer;
      background: linear-gradient(135deg, #5b8def 0%, #3182f6 52%, #1b64da 100%);
      box-shadow: 0 8px 18px rgba(49, 130, 246, 0.28);
      transition: transform 0.22s ease, box-shadow 0.22s ease, filter 0.22s ease, background 0.35s ease;
      -webkit-font-smoothing: antialiased;
    }
    .ai-reply-btn:hover:not(:disabled) {
      transform: translateY(-1px) scale(1.02);
      filter: brightness(1.06);
      box-shadow: 0 12px 24px rgba(49, 130, 246, 0.36);
    }
    .ai-reply-btn:active:not(:disabled) {
      transform: translateY(0) scale(0.98);
    }
    .ai-reply-btn:disabled {
      cursor: default;
      transform: none;
    }
    .ai-reply-btn.is-loading {
      background: linear-gradient(135deg, #7aa7ff 0%, #4b8bff 50%, #3182f6 100%);
      box-shadow: 0 8px 18px rgba(49, 130, 246, 0.22);
    }
    .ai-reply-btn.is-done {
      background: linear-gradient(135deg, #34d399 0%, #10b981 55%, #059669 100%);
      box-shadow: 0 8px 18px rgba(16, 185, 129, 0.28);
    }
    .ai-reply-btn__label {
      display: inline-block;
      transition: opacity 0.22s ease, transform 0.22s ease;
    }
    .ai-reply-btn.is-fading .ai-reply-btn__label {
      opacity: 0;
      transform: translateY(4px);
    }
    .ai-reply-btn__spinner {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      border: 2px solid rgba(255,255,255,0.35);
      border-top-color: #fff;
      animation: ai-reply-spin 0.7s linear infinite;
      display: none;
      flex-shrink: 0;
    }
    .ai-reply-btn.is-loading .ai-reply-btn__spinner {
      display: inline-block;
    }
    @keyframes ai-reply-spin {
      to { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
}

function setButtonLabel(btn, text) {
  const label = btn.querySelector('.ai-reply-btn__label');
  if (!label) {
    btn.textContent = text;
    return Promise.resolve();
  }
  btn.classList.add('is-fading');
  return new Promise((resolve) => {
    window.setTimeout(() => {
      label.textContent = text;
      btn.classList.remove('is-fading');
      window.setTimeout(resolve, 220);
    }, 180);
  });
}

const COMPLAINT_KEYWORDS = [
  '별로', '최악', '실망', '늦었', '늦은', '차갑', '식었', '불친절', '취소', '환불',
  '누락', '빠졌', '잘못', '짜증', '화나', '냄새', '비위생', '적어요', '적어', '짜요',
  '싱거', '딱딱', '탔어', '타서', '배달사고', '연락', '다시는', '비추', '별로예',
  '별로요', '최악이', '후회', '기다리', '안 옴', '안옴', '식어', '차가운', '불만',
  '클레임', '항의', '엉망', '대충', '맛없', '느끼', '느끼해', '기름'
];

const PRAISE_KEYWORDS = [
  '최고', '맛있', '친절', '빠르', '또 시', '재주문', '단골', '감동', '완벽', '굿',
  '추천', '만족', '최고예', '최고요', '존맛', '대박', '최고입', '최고습', '잘 먹',
  '잘먹', '너무 좋', '최고다', '최고네'
];

function stripUiNoise(text) {
  return text
    .replace(IDLE_LABEL, '')
    .replace(ANALYZE_LABEL, '')
    .replace(DONE_LABEL, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function countFilledStars(root) {
  const selectors = [
    '[class*="star"][class*="on"]',
    '[class*="star"][class*="fill"]',
    '[class*="star"][class*="active"]',
    '[class*="Star"][class*="on"]',
    '[aria-checked="true"]',
    'svg[class*="fill"]',
    'img[src*="star"][src*="on"]'
  ];
  let count = 0;
  selectors.forEach((sel) => {
    count = Math.max(count, root.querySelectorAll(sel).length);
  });
  if (count >= 1 && count <= 5) return count;
  return null;
}

function parseStarRating(raw) {
  const text = raw || '';
  const patterns = [
    /별점\s*[:：]?\s*([1-5](?:\.\d)?)/,
    /평점\s*[:：]?\s*([1-5](?:\.\d)?)/,
    /([1-5](?:\.\d)?)\s*점(?!\s*만점)/,
    /([1-5](?:\.\d)?)\s*\/\s*5/,
    /rating[:\s]*([1-5](?:\.\d)?)/i,
    /★{1,5}/,
    /⭐{1,5}/
  ];
  for (const re of patterns) {
    const m = text.match(re);
    if (!m) continue;
    if (m[0].startsWith('★') || m[0].startsWith('⭐')) return m[0].length;
    const n = parseFloat(m[1]);
    if (n >= 1 && n <= 5) return n;
  }
  return null;
}

function findMatchedKeywords(text, keywords) {
  return keywords.filter((word) => text.includes(word));
}

function classifyReview(starRating, reviewText) {
  const complaints = findMatchedKeywords(reviewText, COMPLAINT_KEYWORDS);
  const praises = findMatchedKeywords(reviewText, PRAISE_KEYWORDS);
  const lowStar = starRating != null && starRating <= 3;
  const fiveStar = starRating != null && starRating >= 4.8;

  if (lowStar || complaints.length >= 1) {
    return {
      type: 'negative',
      strategy: '사과와 개선 약속 위주. 변명·반박은 최소화. 지적된 문제를 짧게 인정하고, 재발 방지·개선 조치를 구체적으로 약속. 재주문 유도는 하지 않거나 아주 절제.',
      complaints,
      praises
    };
  }
  if (fiveStar || (praises.length >= 1 && complaints.length === 0 && (starRating == null || starRating >= 4))) {
    return {
      type: 'praise',
      strategy: '감사 인사와 재주문 유도. 칭찬 포인트를 한 가지 짚어 화답하고, 다음에도 찾아달라는 따뜻한 멘트 포함.',
      complaints,
      praises
    };
  }
  return {
    type: 'mixed',
    strategy: '좋은 점은 짧게 감사하고, 아쉬운 점은 사과와 개선 약속. 과한 재주문 유도는 피함.',
    complaints,
    praises
  };
}

function extractReviewContext(textarea) {
  const card = textarea.closest('article, li, [class*="review"], [class*="Review"], section, div') || textarea.parentElement;
  const raw = stripUiNoise(card.innerText || '');
  const ariaBits = [...card.querySelectorAll('[aria-label], [title]')].map((el) => {
    return [el.getAttribute('aria-label'), el.getAttribute('title')].filter(Boolean).join(' ');
  }).join(' ');
  const starFromDom = countFilledStars(card);
  const starFromText = parseStarRating(`${raw} ${ariaBits}`);
  const starRating = starFromDom || starFromText;
  const classification = classifyReview(starRating, raw);
  return {
    reviewText: raw.slice(0, 1800),
    starRating,
    ...classification
  };
}

function buildPrompt(ctx, customPrompt, replyTone) {
  const toneGuide = TONE_INSTRUCTIONS[replyTone] || TONE_INSTRUCTIONS.polite;
  const instruction = customPrompt || '배달 음식점 사장님 답글';
  const starLine = ctx.starRating != null ? `${ctx.starRating}점` : '확인 불가(본문·키워드로 판단)';
  return `[역할] 배달 플랫폼 사장님 답글 작성자. 답글 본문만 출력.

[답글 톤] ${toneGuide}
[매장 지침] ${instruction}

[리뷰 분석]
- 별점: ${starLine}
- 분류: ${ctx.type}
- 불만 키워드: ${ctx.complaints.length ? ctx.complaints.join(', ') : '없음'}
- 칭찬 키워드: ${ctx.praises.length ? ctx.praises.join(', ') : '없음'}
- 작성 전략: ${ctx.strategy}

[고객 리뷰·주변 텍스트]
"""
${ctx.reviewText}
"""

규칙:
- 분류가 negative면 진심 어린 사과 + 개선 약속을 중심으로 쓰고, 자랑·재주문 유도는 넣지 마.
- 분류가 praise(특히 5점·칭찬)면 감사 + 재주문/단골 유도 멘트를 자연스럽게 넣어.
- 리뷰에 나온 메뉴·이슈를 한 가지 이상 구체적으로 언급해.
- 가짜 할인 쿠폰 남발 금지. 마크다운·따옴표 없이 답글만.`;
}

async function generateAIReply(ctx, apiKey, customPrompt, replyTone) {
  const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
  const prompt = buildPrompt(ctx, customPrompt, replyTone);

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
  });

  const data = await response.json();
  if (data.candidates && data.candidates[0].content.parts[0].text) {
    return data.candidates[0].content.parts[0].text.trim();
  }
  throw new Error('답글 생성 실패');
}

function injectAIButtons() {
  ensureButtonStyles();
  const textareas = document.querySelectorAll('textarea:not([data-ai-injected="true"])');
  textareas.forEach((textarea) => {
    textarea.setAttribute('data-ai-injected', 'true');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ai-reply-btn';
    btn.innerHTML = '<span class="ai-reply-btn__spinner" aria-hidden="true"></span><span class="ai-reply-btn__label">' + IDLE_LABEL + '</span>';

    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      if (btn.disabled) return;
      chrome.storage.sync.get(['geminiApiKey', 'customPrompt', 'replyTone'], async (items) => {
        if (!items.geminiApiKey) {
          alert('브라우저 우측 상단 퍼즐 아이콘을 눌러 API 키를 먼저 저장해주세요!');
          return;
        }
        const ctx = extractReviewContext(textarea);

        btn.disabled = true;
        btn.classList.remove('is-done');
        btn.classList.add('is-loading');
        await setButtonLabel(btn, ANALYZE_LABEL);

        try {
          const reply = await generateAIReply(
            ctx,
            items.geminiApiKey,
            items.customPrompt,
            items.replyTone
          );
          textarea.value = reply;
          textarea.dispatchEvent(new Event('input', { bubbles: true }));
          btn.classList.remove('is-loading');
          btn.classList.add('is-done');
          await setButtonLabel(btn, DONE_LABEL);
        } catch (err) {
          alert('오류: ' + err.message);
          btn.classList.remove('is-loading', 'is-done');
          await setButtonLabel(btn, IDLE_LABEL);
          btn.disabled = false;
          return;
        }

        window.setTimeout(async () => {
          btn.classList.remove('is-done', 'is-loading');
          await setButtonLabel(btn, IDLE_LABEL);
          btn.disabled = false;
        }, 2200);
      });
    });
    textarea.parentNode.insertBefore(btn, textarea);
  });
}

injectAIButtons();
const observer = new MutationObserver(() => injectAIButtons());
observer.observe(document.body, { childList: true, subtree: true });
