const TONE_DEFAULT = 'polite';

document.addEventListener('DOMContentLoaded', () => {
  const apiKeyEl = document.getElementById('apiKey');
  const promptEl = document.getElementById('prompt');
  const toastEl = document.getElementById('toast');
  const saveBtn = document.getElementById('saveBtn');

  chrome.storage.sync.get(['geminiApiKey', 'customPrompt', 'replyTone'], (items) => {
    if (items.geminiApiKey) apiKeyEl.value = items.geminiApiKey;
    if (items.customPrompt) promptEl.value = items.customPrompt;
    const tone = items.replyTone || TONE_DEFAULT;
    const radio = document.querySelector('input[name="replyTone"][value="' + tone + '"]');
    if (radio) radio.checked = true;
  });

  saveBtn.addEventListener('click', () => {
    const replyTone = document.querySelector('input[name="replyTone"]:checked')?.value || TONE_DEFAULT;
    chrome.storage.sync.set({
      geminiApiKey: apiKeyEl.value.trim(),
      customPrompt: promptEl.value.trim(),
      replyTone
    }, () => {
      toastEl.textContent = '저장 완료';
      toastEl.classList.add('show');
      setTimeout(() => toastEl.classList.remove('show'), 1600);
    });
  });
});
