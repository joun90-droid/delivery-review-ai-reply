const TONE_INSTRUCTIONS = {
  kind: '톤: 친절하고 감성적. 고객 마음을 따뜻하게 공감하고, 부드럽고 다정한 사장님 말투로 2~4줄 작성.',
  polite: '톤: 정중하고 깔끔. 군더더기 없이 담백한 사장님 말투로 2~3줄 작성. 과도한 이모지·감탄은 피함.',
  firm: '톤: 악플·비난에 단호히 대처. 욕설에 맞대응하지 말고, 사실·사과·개선 의지를 차분하고 단호하게 2~4줄로 작성. 감정 싸움은 금지.',
  short: '톤: 초간단. 반드시 한 문장(1줄)만 작성. 인사와 핵심만.'
};

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
  throw new Error("답글 생성 실패");
}

function injectAIButtons() {
  const textareas = document.querySelectorAll('textarea:not([data-ai-injected="true"])');
  textareas.forEach((textarea) => {
    textarea.setAttribute('data-ai-injected', 'true');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = '✨ AI 답글 생성';
    btn.style.cssText = 'margin: 5px 0; padding: 5px 10px; background: #2ac1bc; color: white; border: none; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer; display: block;';

    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      chrome.storage.sync.get(['geminiApiKey', 'customPrompt', 'replyTone'], async (items) => {
        if (!items.geminiApiKey) {
          alert('브라우저 우측 상단 퍼즐 아이콘을 눌러 API 키를 먼저 저장해주세요!');
          return;
        }
        const parentCard = textarea.closest('div, li, section') || textarea.parentElement;
        const reviewText = parentCard.innerText.replace('✨ AI 답글 생성', '').trim();

        btn.innerText = '⏳ 작성 중...';
        btn.disabled = true;
        try {
          const reply = await generateAIReply(
            reviewText,
            items.geminiApiKey,
            items.customPrompt,
            items.replyTone
          );
          textarea.value = reply;
          textarea.dispatchEvent(new Event('input', { bubbles: true }));
          btn.innerText = '✅ 완료';
        } catch (err) {
          alert('오류: ' + err.message);
          btn.innerText = '✨ AI 답글 생성';
        } finally {
          btn.disabled = false;
          setTimeout(() => { btn.innerText = '✨ AI 답글 생성'; }, 2500);
        }
      });
    });
    textarea.parentNode.insertBefore(btn, textarea);
  });
}

injectAIButtons();
const observer = new MutationObserver(() => injectAIButtons());
observer.observe(document.body, { childList: true, subtree: true });