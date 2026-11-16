# CELIKOM Android A1 — exact Media3 Player ancestry audit

**Дата:** 16.11.2026  
**Репозиторий:** `manufact-test/nomusic`  
**Рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Latest audit checkpoint:** `c0cf9896916cca9b13299cdb3fde7a78ffbe4da1`  
**CI #213:** [SUCCESS, 127/127 тестов](https://github.com/manufact-test/nomusic/actions/runs/43871788563)  
**Точный backup:** `backup/android-a1-playlist-callback-route-closed-ci-green-20261116` @ `c0cf9896916cca9b13299cdb3fde7a78ffbe4da1`

Read-only анализ точного issuer-signed Yandex 2025 XAPK, шесть DEX. Runtime hooks, приложение, APK и playback не затрагивались.

> **Latest superseding result:** маршрут `LXk6.if(LsO7;LXi6$e;Ljava/util/List;)V` закрыт как непригодный для доказательства TrackWrapper → active Player item. Внутренний List.get → MediaItem → Player setter identity доказан, но direct callers/MethodHandle отсутствуют; interface contract имеет шесть concrete implementers, runtime dispatch к LXk6 не доказан, а List прослежен только до поля LKl6. Текущий статус и следующий узкий маршрут — в [ANDROID-A1-PLAYLIST-CALLBACK-ROUTE-CLOSURE-20261116.md](ANDROID-A1-PLAYLIST-CALLBACK-ROUTE-CLOSURE-20261116.md) и [ANDROID-A1-MEDIAITEM-PLAYER-PLAYLIST-HANDOFF-20261116.md](ANDROID-A1-MEDIAITEM-PLAYER-PLAYLIST-HANDOFF-20261116.md). Не повторять этот route census.

