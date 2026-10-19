(function () {
  'use strict';
  const status = document.getElementById('status');
  const candidates = document.getElementById('candidates');
  const media = document.getElementById('media');
  const events = document.getElementById('events');
  const seconds = document.getElementById('session-time');
  const copy = document.getElementById('copy');
  const reset = document.getElementById('reset');
  const labels = {
    banner: 'Баннер (кандидат)', overlay: 'Окно (кандидат)',
    video: 'Видео (кандидат)', audio: 'Аудио (кандидат)',
    play: 'старт', playing: 'проигрывание', pause: 'пауза',
    ended: 'завершение', waiting: 'ожидание', stalled: 'зависание', error: 'ошибка',
    'ad-heard': 'отмечена звуковая реклама', 'normal-music': 'отмечена обычная музыка',
    'video-ad-seen': 'отмечена видеореклама', 'popup-ad-seen': 'отмечено рекламное окно'
  };
  let last = null;

  function row(parent, title, value) {
    const dt = document.createElement('dt'), dd = document.createElement('dd');
    dt.textContent = title; dd.textContent = String(value);
    parent.append(dt, dd);
  }
  function render(data) {
    last = data;
    candidates.replaceChildren();
    media.replaceChildren();
    events.replaceChildren();
    for (const kind of ['banner', 'overlay', 'video', 'audio']) {
      row(candidates, labels[kind], data.candidates[kind] || 0);
    }
    for (const kind of ['audio', 'video']) {
      const counts = data.media[kind] || {};
      const name = kind === 'audio' ? 'Аудио' : 'Видео';
      row(media, name + ' • старт', (counts.play || 0) + (counts.playing || 0));
      row(media, name + ' • остановки/ошибки',
        (counts.waiting || 0) + (counts.stalled || 0) + (counts.error || 0));
      row(media, name + ' • завершение', counts.ended || 0);
    }
    row(media, 'Пропущенные узлы (лимит нагрузки)', data.droppedRoots || 0);
    seconds.textContent = '(' + data.ageSeconds + ' с)';
    document.getElementById('marker-count').textContent = 'Ручных отметок: ' + (data.markers?.length || 0);
    for (const item of data.recent.slice(-12).reverse()) {
      const li = document.createElement('li');
      const description = item.category === 'candidate'
        ? 'найден кандидат: ' + (labels[item.kind] || item.kind)
        : item.category === 'marker' ? (labels[item.kind] || 'отметка')
        : item.kind + ': ' + (labels[item.event] || 'событие');
      li.textContent = '+' + item.s + ' с — ' + description;
      events.appendChild(li);
    }
    if (!events.children.length) {
      const li = document.createElement('li');
      li.textContent = 'Событий пока нет';
      events.appendChild(li);
    }
    copy.disabled = false;
    reset.disabled = false;
    status.textContent = 'Подключено. Режим только для наблюдения.';
  }
  async function send(type, kind) {
    // Query tab ID only: do not request/read tab URL, title or favicon.
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    if (!tab || !Number.isInteger(tab.id)) throw Error('No active tab');
    return chrome.tabs.sendMessage(tab.id, kind === undefined ? {type} : {type, kind});
  }
  async function refresh(type = 'CELIKOM_OBSERVER_GET') {
    status.textContent = 'Обновляю счётчики…';
    try {
      const data = await send(type);
      if (!data || data.schema !== 'celikom-ad-observer-v1') throw Error('Observer missing');
      render(data);
    } catch (_) {
      last = null; copy.disabled = true; reset.disabled = true;
      status.textContent = 'Открой music.yandex.ru и перезагрузи вкладку. Наблюдатель работает только там.';
    }
  }
  for (const button of document.querySelectorAll('[data-marker]')) {
    button.addEventListener('click', async () => {
      const kind = button.getAttribute('data-marker');
      try {
        const response = await send('CELIKOM_OBSERVER_MARK', kind);
        if (response?.schema !== 'celikom-ad-observer-v1') throw Error('No observer');
        render(response);
      } catch (_) { status.textContent = 'Не удалось записать отметку: открой вкладку Яндекс Музыки.'; }
    });
  }
  document.getElementById('refresh').addEventListener('click', () => refresh());
  reset.addEventListener('click', () => refresh('CELIKOM_OBSERVER_RESET'));
  copy.addEventListener('click', async () => {
    if (!last) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(last, null, 2));
      status.textContent = 'Обезличенные счётчики скопированы.';
    } catch (_) {
      status.textContent = 'Копирование недоступно. Проверь доступ к буферу обмена.';
    }
  });
  refresh();
})();
