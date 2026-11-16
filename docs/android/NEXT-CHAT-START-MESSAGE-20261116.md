Привет! Принимай **CELIKOM Android A1** как ведущий разработчик. Продолжай строго с сохранённой точки: не начинай с нуля и не меняй архитектуру.

**GitHub:** `manufact-test/nomusic`  
**Ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Code checkpoint:** `27ccbe8348d598fead0386e70ef68573b04270c4`  
**Code backup:** `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116`  
**CI #229:** [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139) — Yandex 2025.10.4 #120.1gpr, 16 splits / 6 DEX.  
**CI #230:** [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101) — compact logs; full JSON deleted.  
**Last runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`; no later hook changes.

### Прочитай только два документа

1. `docs/android/NEXT-CHAT.md` — единственный актуальный статус.
2. `docs/android/ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md` — последняя техническая точка.

`docs/android/README.md` — индекс. Старые NEXT-CHAT/HANDOFF и архивы не загружай при старте.

### Не путай три версии Яндекса

- **2025.10.4 #120.1gpr / code 24025542:** подписанный образец 16 splits / 6 DEX; LSPatch2 lab input и текущий CI #229. Не доказан как финальный target CELIKOM.
- **2026.10.3 #170gpr / code 24026531:** подписанный оригинал 5 splits; original-only native ARM13 control CI #42990078186. SHA-256 XAPK: `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`. Есть отдельный structural clone helper, но product target не подтверждён.
- **2026.09.5 #167gpr / #167.1gpr:** ранее сообщённая версия на телефоне; точный оригинальный пакет/SHA не закреплён.

**Target build CELIKOM A1 не установлен.** Manifest `<queries><package name="ru.yandex.music"/></queries>` означает package visibility; сам по себе он не доказывает, что Yandex embedded или absent.

### Первая задача

Проверь реальный A1 packaging/build pipeline, workflow inputs, origin/source package references, split merge scripts и историю артефактов. Установи, какая версия реально является source/runtime target CELIKOM. Сопоставь все три версии и их роли. Не задавай старый вопрос только «2025 или 2026.09.5?». Если repo не даёт ответа, задай один вопрос, перечислив все три кандидата и доказательства.

Перед анализом выбранного бинарника проверь publisher signature, package/version/versionCode, полный split set, size и SHA-256. Не переноси обфусцированные дескрипторы между версиями.

### Затем — LfT2

Текущая цепочка доказана **только на 2025.10.4 #120.1gpr**:

`LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>`

До MediaSource/Player/decoder same-object handoff не доказан. После выбора target продолжи только с точным `LfT2;` в соответствующем подписанном DEX. Учитывай прямой MediaSource path в Media3; требуй object identity. Не повторяй закрытые LiLb и LXk6.

### Статус и ограничения

- **Stage A / NAV17: PASS** по подтверждению владельца 14 Nov — оригинальная музыка Яндекса работает.
- **Stage B: NO-GO** — CELIKOM replacement audio не подключён и не подтверждён.
- Только Android A1. Не менять архитектуру, runtime hooks, APK и оригинальный Яндекс; не добавлять второй Player/decoder/AudioTrack.
- Не читать IDs, названия, URL, DataSpec, токены, account data, приватные значения полей или audio bytes.
- Не трогать Test.50, frozen A1/LSPatch, Windows, extension, backend/API/DB и production.
- Работай крупным законченным блоком, без промежуточных отчётов и полных CI-логов.

**Источник истины — NEXT-CHAT.md.** Все старые handoffs — исторические материалы.
