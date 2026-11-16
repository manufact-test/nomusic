Привет! Ты принимаешь **CELIKOM Android A1** как ведущий разработчик. Продолжай строго с текущего состояния. Ничего не начинай с нуля и архитектуру не меняй.

**GitHub:** `manufact-test/nomusic`  
**Рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Последний code checkpoint:** `27ccbe8348d598fead0386e70ef68573b04270c4`  
**Code backup:** `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116`  
**CI #229:** [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139) — 2025.10.4 #120.1gpr, 16 splits / 6 DEX, read-only.  
**CI #230:** [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101) — compact logs, full JSON deleted after summary.  
**Последний runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`; после него hooks не менялись.

### Прочитай только два документа

1. `docs/android/NEXT-CHAT.md` — единственный актуальный handoff.
2. `docs/android/ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md` — последняя техническая точка.

Для навигации есть `docs/android/README.md`. Не читай архивы и старые NEXT-CHAT/HANDOFF файлы при старте.

### Важная хронология версий — не путай роли

- **2025.10.4 #120.1gpr / code 24025542:** подписанный образец 16 splits / 6 DEX; LSPatch2 lab input и текущий CI #229 static LfT2 specimen. Это не доказанный финальный target CELIKOM.
- **2026.10.3 #170gpr / code 24026531:** подписанный оригинал 5 splits; native ARM13 original-only control CI #42990078186. XAPK SHA-256 `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`. Также есть отдельный structural clone helper, но product target не подтверждён.
- **2026.09.5 #167gpr / #167.1gpr:** ранее сообщённая версия на телефоне; точный оригинальный пакет/SHA не закреплён.

**Target build CELIKOM A1 пока не установлен.** Не задавай владельцу старый вопрос только между 2025.10.4 и 2026.09.5. Сначала сопоставь все три доказательных роли с реальным packaging/build pipeline. Manifest `<queries><package name="ru.yandex.music"/></queries>` означает package visibility и сам по себе не доказывает, что Yandex embedded или absent.

### Первая задача

Проверь текущий A1 packaging, workflow inputs, origin/source package references, split merge scripts и историю точных артефактов. Установи, какая версия реально является source/runtime target CELIKOM. Если репозиторий не даёт ответа, задай один вопрос, перечислив все три версии и их роли. Не выбирай версию по принципу «самая новая».

Перед анализом выбранного бинарника проверь publisher signature, package/version/versionCode, полный split set, size и SHA-256.

### Следующая техническая задача — после выбора бинарника

Продолжай с `LfT2;` только на подтверждённой версии. Текущая цепочка доказана на 2025.10.4 #120.1gpr:

`LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>`

До Player/source/decoder same-object handoff не доказан. Не переноси обфусцированные дескрипторы на другой build.

Учитывай Media3 direct MediaSource path; не зацикливайся на MediaItem. Требуй доказательства идентичности объекта. Не повторяй закрытые LiLb и LXk6.

### Статус и ограничения

- Stage A / NAV17: PASS по подтверждению владельца 14 Nov — оригинальная музыка Яндекса работает.
- Stage B: NO-GO — CELIKOM replacement audio не подключён и не подтверждён.
- Только Android A1. Не менять архитектуру, runtime hooks, APK и оригинальный Яндекс.
- Не добавлять второй Player/decoder/AudioTrack.
- Не читать IDs, названия, URL, DataSpec, токены, account data, приватные значения полей или audio bytes.
- Не трогать Test.50, frozen A1/LSPatch, Windows, extension, backend/API/DB и production.
- Работай крупным законченным блоком, без промежуточных отчётов. Не загружай полные CI-логи или гигантские файлы.

**Главное:** сначала установи правильный target build, затем продолжай LfT2. NEXT-CHAT.md — источник актуального состояния; все старые handoffs — исторические материалы.
