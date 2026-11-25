/* Only bounded public error codes cross from the worker into popup text. */
const messages = Object.freeze({
  track_required: 'Сначала запустите песню в Яндекс Музыке.',
  sign_in_required: 'Войдите в аккаунт, чтобы включить подмену музыки.',
  auth_timeout: 'Сервер не ответил вовремя. Повторите «Старт».',
  auth_network_error: 'Не удалось соединиться с сервером CELIKOM. Проверьте подключение и VPN, затем повторите «Старт».',
  auth_route_blocked: 'Запрос к CELIKOM заблокирован. Проверьте подключение и VPN, затем повторите «Старт».',
  auth_unavailable: 'Не удалось проверить доступ CELIKOM. Повторите «Старт»; если ошибка останется, отправьте сообщение в поддержку.',
  account_disabled: 'Доступ к аккаунту отключён. Обратитесь в поддержку.',
  email_unverified: 'Подтвердите почту аккаунта, чтобы включить подмену музыки.',
  trial_inactive: 'Пробный период завершён. Проверьте доступ в аккаунте CELIKOM.',
  entitlement_inconsistent: 'Не удалось подтвердить данные доступа. Обратитесь в поддержку CELIKOM.',
  api_forbidden: 'Подмена недоступна для этого аккаунта. Проверьте доступ в CELIKOM.',
  rate_limited: 'Слишком много попыток. Подождите немного и повторите «Старт».',
  extension_update_required: 'Обновите расширение CELIKOM и перезагрузите вкладку Яндекс Музыки.'
});
export function startAccessError(code): string {
  if (code === 'invalid_session') return 'sign_in_required';
  return typeof code === 'string' && Object.hasOwn(messages, code) ? code : 'auth_unavailable';
}
export function startAccessMessage(code): string { return messages[startAccessError(code)]; }

