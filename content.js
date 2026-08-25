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

async function generateAIReply(reviewText, apiKey, customPrompt, replyTone) {
  const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
  const toneGuide = TONE_INSTRUCTIONS[replyTone] || TONE_INSTRUCTIONS.polite;
  const instruction = customPrompt || '배달 음식점 사장님 답글';
  const prompt = `[답글 톤]: ${toneGuide}\n[매장 지침]: ${instruction}\n\n[고객 리뷰]: "${reviewText}"\n\n위 리뷰에 대한 사장님 맞춤 답글만 작성해줘. 답글 본문만 출력.`;

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
        const parentCard = textarea.closest('div, li, section') || textarea.parentElement;
        const reviewText = parentCard.innerText
          .replace(IDLE_LABEL, '')
          .replace(ANALYZE_LABEL, '')
          .replace(DONE_LABEL, '')
          .trim();

        btn.disabled = true;
        btn.classList.remove('is-done');
        btn.classList.add('is-loading');
        await setButtonLabel(btn, ANALYZE_LABEL);

        try {
          const reply = await generateAIReply(
            reviewText,
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
