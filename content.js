const TONE_INSTRUCTIONS = {
  kind: '톤: 친절하고 감성적. 따뜻한 공감, 다정한 사장님 말투로 2~4줄.',
  polite: '톤: 정중하고 깔끔. 담백한 사장님 말투. 과도한 이모지 금지. 2~3줄.',
  firm: '톤: 악플·오해에 단호히 대처. 욕설 맞대응 금지. 사실·사과·개선을 차분하고 단호하게.',
  short: '톤: 초간단. 반드시 한 문장(1줄)만.'
};

const COMPLAINT_KEYWORDS = [
  '별로', '최악', '실망', '늦었', '늦은', '차갑', '식었', '불친절', '취소', '환불',
  '누락', '빠졌', '잘못', '짜증', '화나', '냄새', '비위생', '적어요', '짜요',
  '싱거', '딱딱', '타서', '배달사고', '다시는', '비추', '후회', '맛없', '불만', '엉망'
];

const PRAISE_KEYWORDS = [
  '최고', '맛있', '친절', '빠르', '재주문', '단골', '감동', '완벽', '굿', '추천',
  '만족', '존맛', '대박', '잘 먹', '너무 좋'
];

function ensureButtonStyles() {
  if (document.getElementById('ai-reply-btn-styles')) return;
  const style = document.createElement('style');
  style.id = 'ai-reply-btn-styles';
  style.textContent = `
    .ai-reply-btn {
      display: inline-flex; align-items: center; justify-content: center; gap: 6px;
      margin: 8px 0 10px; padding: 8px 14px; border: none; border-radius: 999px;
      color: #fff; font-size: 12px; font-weight: 700; letter-spacing: -0.2px;
      font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif;
      cursor: pointer;
      background: linear-gradient(135deg, #5b8def 0%, #3182f6 52%, #1b64da 100%);
      box-shadow: 0 8px 16px rgba(49,130,246,0.28);
      transition: transform .2s ease, filter .2s ease, background .3s ease;
    }
    .ai-reply-btn:hover:not(:disabled) { transform: translateY(-1px); filter: brightness(1.06); }
    .ai-reply-btn:disabled { cursor: default; transform: none; }
    .ai-reply-btn.is-loading { opacity: 0.92; }
    .ai-reply-btn.is-done {
      background: linear-gradient(135deg, #34d399, #10b981 55%, #059669);
    }
  `;
  document.head.appendChild(style);
}

function stripUiNoise(text) {
  return String(text || '')
    .replace(/✨\s*AI 답글 생성/g, '')
    .replace(/⏳\s*작성 중\.\.\./g, '')
    .replace(/✅\s*완료/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function parseStarRating(raw) {
  const text = raw || '';
  const patterns = [
    /별점\s*[:：]?\s*([1-5](?:\.\d)?)/,
    /평점\s*[:：]?\s*([1-5](?:\.\d)?)/,
    /([1-5](?:\.\d)?)\s*점/,
    /([1-5](?:\.\d)?)\s*\/\s*5/,
    /★{1,5}/,
    /⭐{1,5}/
  ];
  for (const re of patterns) {
    const m = text.match(re);
    if (!m) continue;
    if (m[0][0] === '★' || m[0][0] === '⭐') return m[0].length;
    const n = parseFloat(m[1]);
    if (n >= 1 && n <= 5) return n;
  }
  return null;
}

function extractReviewContext(textarea) {
  const card = textarea.closest('article, li, [class*="review"], [class*="Review"], section, div') || textarea.parentElement;
  const raw = stripUiNoise(card.innerText || '');
  const aria = [...card.querySelectorAll('[aria-label], [title]')].map((el) => {
    return [el.getAttribute('aria-label'), el.getAttribute('title')].filter(Boolean).join(' ');
  }).join(' ');
  const starRating = parseStarRating(raw + ' ' + aria);
  const complaints = COMPLAINT_KEYWORDS.filter((w) => raw.includes(w));
  const praises = PRAISE_KEYWORDS.filter((w) => raw.includes(w));
  let strategy = '감사와 재방문을 자연스럽게.';
  if ((starRating != null && starRating <= 3) || complaints.length) {
    strategy = '사과와 개선 약속 위주. 재주문 유도는 절제.';
  } else if ((starRating != null && starRating >= 4.8) || praises.length) {
    strategy = '감사와 재주문 유도.';
  }
  return { reviewText: raw.slice(0, 1800), starRating, complaints, praises, strategy };
}

async function generateAIReply(ctx, apiKey, customPrompt, replyTone) {
  const endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=' + encodeURIComponent(apiKey);
  const toneGuide = TONE_INSTRUCTIONS[replyTone] || TONE_INSTRUCTIONS.polite;
  const shop = customPrompt || '배달 음식점 사장님';
  const starLine = ctx.starRating != null ? ctx.starRating + '점' : '확인 불가';
  const prompt = `[역할] 배달 플랫폼 사장님 답글. 답글 본문만 출력.
[답글 톤] ${toneGuide}
[매장 지침] ${shop}
[별점] ${starLine}
[불만 키워드] ${ctx.complaints.join(', ') || '없음'}
[칭찬 키워드] ${ctx.praises.join(', ') || '없음'}
[전략] ${ctx.strategy}
[고객 리뷰]
"""
${ctx.reviewText}
"""
자연스러운 사장님 맞춤 답글만 작성.`;

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
  });
  const data = await response.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) throw new Error(data?.error?.message || '답글 생성 실패');
  return text.trim();
}

function injectValue(textarea, value) {
  const proto = window.HTMLTextAreaElement && window.HTMLTextAreaElement.prototype;
  const setter = proto && Object.getOwnPropertyDescriptor(proto, 'value')?.set;
  if (setter) setter.call(textarea, value);
  else textarea.value = value;
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
  textarea.dispatchEvent(new Event('change', { bubbles: true }));
}

function injectAIButtons() {
  ensureButtonStyles();
  document.querySelectorAll('textarea:not([data-ai-injected="true"])').forEach((textarea) => {
    textarea.setAttribute('data-ai-injected', 'true');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ai-reply-btn';
    btn.textContent = '✨ AI 답글 생성';

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (btn.disabled) return;

      chrome.storage.sync.get(['geminiApiKey', 'customPrompt', 'replyTone'], async (items) => {
        if (!items.geminiApiKey) {
          alert('확장 프로그램 아이콘을 눌러 Gemini API 키를 먼저 저장해주세요.');
          return;
        }
        const ctx = extractReviewContext(textarea);
        btn.disabled = true;
        btn.classList.remove('is-done');
        btn.classList.add('is-loading');
        btn.textContent = '⏳ 작성 중...';
        try {
          const reply = await generateAIReply(ctx, items.geminiApiKey, items.customPrompt, items.replyTone);
          injectValue(textarea, reply);
          btn.classList.remove('is-loading');
          btn.classList.add('is-done');
          btn.textContent = '✅ 완료';
        } catch (err) {
          alert('오류: ' + err.message);
          btn.classList.remove('is-loading', 'is-done');
          btn.textContent = '✨ AI 답글 생성';
          btn.disabled = false;
          return;
        }
        setTimeout(() => {
          btn.classList.remove('is-done', 'is-loading');
          btn.textContent = '✨ AI 답글 생성';
          btn.disabled = false;
        }, 2200);
      });
    });

    textarea.parentNode.insertBefore(btn, textarea);
  });
}

injectAIButtons();
const observer = new MutationObserver(() => injectAIButtons());
observer.observe(document.documentElement, { childList: true, subtree: true });
