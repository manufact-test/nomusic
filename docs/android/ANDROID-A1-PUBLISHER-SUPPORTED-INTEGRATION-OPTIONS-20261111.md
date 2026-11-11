> **11.11.2026 independent verification/decision record:** [native UI publisher rights decision gate](ANDROID-A1-PUBLISHER-RIGHTS-NATIVE-UI-DECISION-GATE-20261111.md) compares an authorized native SDK against public Android MediaSession, external Activity and unsuitable alternatives, with exact evidence and written technical acceptance questions. No outreach has been sent. Current Stage A remains NO-GO; this page's message is still a DRAFT requiring explicit owner consent.\n\n# CELIKOM Android A1 — official native integration/rights research — 11 November 2026

This is a factual publisher integration investigation, NOT legal advice and NOT a change to the approved CELIKOM product scope.

## Confirmed public evidence

1. Official Yandex.Music **mobile software license**, current source https://yandex.ru/legal/music_mobile_agreement/ru/ (sections 4.1–4.4): program modification, derivative usage and commercial or changed-format redistribution are restricted without written rightsholder consent, except where the license or applicable legislation allows. Owning a license to an alternative audio recording does NOT grant a license to redistribute a modified third-party app.
2. **Archived job ad for Android developer in Yandex.Music**, https://yandex.ru/jobs/vacancies/androidrazrabotchik-v-yandeks-muziku-_moya-volna_-11544 specifically mentions an SDK for embedding music **in other Yandex applications**. This shows an internal integration direction, NOT a public third-party SDK, not a documented UI/API contract, and not authorization for a separately signed full native Yandex UI.
3. Official music support entry https://yandex.ru/support/music/ru/write-to-support has a chat and “other question” route. This can be used to request a **contact for product/business integration**, NOT to presume an ordinary support agent can grant distribution rights.
4. Yandex.Music rightsholder track publishing https://yandex.ru/support/music/ru/performers-and-copyright-holders/terms documents distributor delivery, which is NOT an embedding SDK, single-decoder swap or full native UI route.

As of this research, **no public third-party license/SDK documentation was verified** that provides full native Yandex player UI, MyWave/login and callback selecting a licensed alternative recording inside its original single decoder. This is **not evidence that a private SDK or partner contract cannot exist**. The public job reference is specifically restricted to other applications of Yandex.

## Concrete questions for the rightsholder / partner team

- Can a separately signed, independently named Android application include the fully native Yandex.Music UI + user login + recommendations/MyWave under a specific agreement or official SDK?
- Are publisher-signed components or supported intents available without redistributing/altering proprietary APK files, and can they meet the one-CELIKOM-APK requirement?
- Can a licensed alternative recording be selected **within the one official audio decoder**, without a concurrent second player, while preserving seek/next/background/MyWave?
- What rights and guarantees are needed for recording licenses, subscriptions/authentication, trademark, Play Protect, distribution countries and updates? Would such an integration require a formal partnership?
- If SDK is internal Yandex-only, where should independent third-party developers request a clear feasibility answer?

## OPTIONAL message draft for owner approval only — NOT SENT

Subject: Official Android Yandex.Music player integration / B2B SDK inquiry

Здравствуйте!

Мы изучаем возможность официальной партнёрской интеграции Яндекс.Музыки в отдельное Android-приложение. Хотели бы уточнить, предусмотрен ли у вас SDK или лицензируемая интеграция для сторонних разработчиков, сохраняющая нативный интерфейс, авторизацию, «Мою волну» и штатное управление воспроизведением.

Наш технический сценарий также предполагает согласованный выбор лицензионно разрешённой аудиозаписи в рамках единственного штатного декодера для определённых треков. Мы не планируем обходить подписи/DRM, использовать пользовательские токены или распространять модифицированное ПО без согласования.

Подскажите, доступен ли подобный формат сотрудничества, и с кем из команды партнёрских интеграций можно обсудить технические и юридические требования? Если такой сценарий не поддерживается, будем благодарны за прямой ответ.

Спасибо!

This is a prepared sample, not a message sent or a connection initiated on behalf of the user.

## Product decision

The independently signed cloned Yandex native MAIN voluntarily self-exits on real ARM Android13 across FIVE-split, merged ONE-APK and LSPatch ZERO variants. See https://github.com/manufact-test/nomusic/actions/runs/42991987803 and https://github.com/manufact-test/nomusic/issues/41. The signed original remains alive and OWN LSPatch host works. This *does not prove the exact vendor cause*.

Only official/authorized integration can resolve publisher/rights barriers. If it cannot satisfy one APK, native UI and original single decoder, escalate this **external dependency** for explicit owner approval before any architecture change. Do not silently substitute WebView, two players or demand an extra device.
