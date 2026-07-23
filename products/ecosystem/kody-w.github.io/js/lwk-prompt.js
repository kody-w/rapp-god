// Learn with Kody — copy-prompt button
(function () {
  'use strict';

  function highlightPrompt(prompt) {
    const encodedHighlights = prompt.dataset.highlights;
    if (!encodedHighlights) return;

    let highlights;
    try {
      highlights = JSON.parse(encodedHighlights);
    } catch (error) {
      return;
    }

    if (!Array.isArray(highlights)) highlights = [highlights];
    const terms = Array.from(new Set(highlights.filter((term) => typeof term === 'string' && term.length)))
      .sort((left, right) => right.length - left.length);
    if (!terms.length) return;

    const escapePattern = (term) => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp(terms.map(escapePattern).join('|'), 'g');
    const text = prompt.textContent;
    const fragment = document.createDocumentFragment();
    let offset = 0;
    let match;

    while ((match = pattern.exec(text)) !== null) {
      fragment.appendChild(document.createTextNode(text.slice(offset, match.index)));
      const mark = document.createElement('mark');
      mark.className = 'lwk-prompt-key';
      mark.textContent = match[0];
      fragment.appendChild(mark);
      offset = match.index + match[0].length;
    }

    if (!offset) return;
    fragment.appendChild(document.createTextNode(text.slice(offset)));
    prompt.textContent = '';
    prompt.appendChild(fragment);
  }

  function restoreSelection(selection, ranges) {
    if (!selection) return;
    try {
      selection.removeAllRanges();
      ranges.forEach((range) => selection.addRange(range));
    } catch (error) {
      // A saved range can become stale if the page changes during a copy.
    }
  }

  function focusWithoutScrolling(element) {
    if (!element || typeof element.focus !== 'function') return;
    try {
      element.focus({ preventScroll: true });
    } catch (error) {
      try {
        element.focus();
      } catch (focusError) {
        // Copying can still succeed when a sandbox blocks scripted focus.
      }
    }
  }

  function legacyCopy(text) {
    const textarea = document.createElement('textarea');
    const selection = window.getSelection ? window.getSelection() : null;
    const ranges = [];
    const activeElement = document.activeElement;

    if (selection) {
      for (let index = 0; index < selection.rangeCount; index += 1) {
        ranges.push(selection.getRangeAt(index).cloneRange());
      }
    }

    textarea.value = text;
    textarea.readOnly = true;
    textarea.setAttribute('aria-hidden', 'true');
    textarea.style.position = 'fixed';
    textarea.style.top = '0';
    textarea.style.left = '-9999px';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);

    let copied = false;
    try {
      focusWithoutScrolling(textarea);
      textarea.select();
      textarea.setSelectionRange(0, textarea.value.length);
      copied = typeof document.execCommand === 'function' && document.execCommand('copy');
    } catch (error) {
      copied = false;
    } finally {
      textarea.remove();
      restoreSelection(selection, ranges);
      focusWithoutScrolling(activeElement);
    }

    return copied;
  }

  async function copyText(text) {
    try {
      if (window.isSecureContext && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch (error) {
      // Sandboxed iframes can expose the API while denying clipboard access.
    }
    return legacyCopy(text);
  }

  function selectPrompt(prompt) {
    const selection = window.getSelection && window.getSelection();
    if (!selection || !document.createRange) return;
    focusWithoutScrolling(prompt);
    const range = document.createRange();
    range.selectNodeContents(prompt);
    selection.removeAllRanges();
    selection.addRange(range);
  }

  document.querySelectorAll('.lwk-prompt-text').forEach(highlightPrompt);

  document.querySelectorAll('.lwk-copy-btn').forEach((btn) => {
    const section = btn.closest('.lwk-prompt');
    const prompt = section && section.querySelector('.lwk-prompt-text');
    if (!prompt) return;

    const label = btn.querySelector('.lwk-copy-label');
    const status = section.querySelector('.lwk-copy-status');
    const originalLabel = label ? label.textContent : 'Copy prompt';
    let resetTimer;

    btn.addEventListener('click', async () => {
      window.clearTimeout(resetTimer);
      if (status) status.textContent = '';
      const copied = await copyText(prompt.textContent);

      if (copied) {
        btn.classList.add('is-copied');
        if (label) label.textContent = 'Copied';
        if (status) status.textContent = 'Prompt copied to clipboard.';
      } else {
        btn.classList.remove('is-copied');
        selectPrompt(prompt);
        if (label) label.textContent = 'Press Ctrl/Cmd+C';
        if (status) status.textContent = 'Automatic copy is unavailable. The complete prompt is selected; press Control or Command plus C to copy.';
      }

      resetTimer = window.setTimeout(() => {
        btn.classList.remove('is-copied');
        if (label) label.textContent = originalLabel;
      }, copied ? 1600 : 5000);
    });
  });
})();
