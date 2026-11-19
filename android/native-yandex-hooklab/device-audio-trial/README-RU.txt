CELIKOM Android A1 — NAV42. Read-only сравнение текущего оригинального PlaybackInfo PeriodID с активным SLOT_B при -4 с НЕИЗВЕСТНЫМ EOS.

Установить поверх NAV41 без удаления данных. При несовпадении подписи — остановиться, НЕ удалять приложение. Оригинал Яндекс.Музыки, плеер, декодер и звук не изменяются.

Результат NAV41 на реальном HONOR 50: активный SLOT_B type1/state2/-4=MANY, PLAYER_PERIOD_AT_AUDIO_READ=REGISTERED, но BUFFER_EOS_ACCESS=NO_HOOK. Поэтому прежние строго non-EOS счётчики периода остались NONE.

NAV42 не подделывает EOS. Он отдельно считает структурные совпадения только при точном оригинальном активном SLOT_B, type1/state2/-4, EOS неизвестен. Счётчики PLAYER_PERIOD_EOS_UNKNOWN_SAME_REF / UID_INTS / UID_ONLY / DIFFERENT / UNAVAILABLE. Все прежние счётчики non-EOS оставлены. Сравнение НЕ доказывает выбранный трек/редакцию, новую генерацию очереди или звуковой сэмпл.

Проверь 2–5 треков, Мою волну, Next, паузу, перемотку и повтор той же песни. Сохрани TXT диагностику CELIKOM и пришли её в чат.
Маркер: NAV_V42_PLAYER_PERIOD_SLOTB_EOS_UNKNOWN_READONLY.
CELIKOM_REPLACEMENT=NOT_CONNECTED; IDENTITY_STATUS=STRUCTURAL_ONLY.
