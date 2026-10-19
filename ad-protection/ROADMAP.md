# Ad Protection — roadmap and gate criteria

Date: 2026-10-19. Product goal: all observed forms of Yandex Music advertising in the validated browser environment, without playback regression. Zero integration with CELIKOM until a separately authorized final stage.

| Stage | Status | Work | Acceptance |
|---|---|---|---|
| **0. Preparation** | **COMPLETE** | Set independent folder, plans, standalone no-op MV3 shell, isolated tests and next-chat handoff | Files live only in ad-protection/; no production entrypoints changed |
| **1. Feasibility & policy** | NEXT | Map banners/popups/video/audio ads; inspect supported MV3 APIs, current store rules, Yandex terms, existing code and licenses | Reproducible evidence + GO/NO-GO and risks for every category |
| **2. Standalone prototype** | NOT STARTED | Create a self-contained Chrome MV3 extension with optional feature flags, minimal permissions, diagnostics and fail-open | Loads independently; never imports production player code |
| **3. Visual advertising** | NOT STARTED | Implement scoped DOM handling + optional tested request rules for banners/overlays/video | No observed visual ad remains across defined tests; ordinary UI intact |
| **4. Audio advertising** | NOT STARTED | Investigate precise audio ad signals and safe handling without corrupting audio playback | All observed audio ad scenarios handled; originals, seeking and queues unaffected. Otherwise NO-GO/RESEARCH BLOCKER |
| **5. Reliability & stress** | NOT STARTED | Long listening, reload/SPA navigation, tabs, network faults, regional variants, performance, independent module-off regression | Pass test matrix and no disruptive side effects |
| **6. Distribution review** | NOT STARTED | Full permissions / security / licensing / policy review, packaging, test publication when authorized | Explicit decision on publishability; approval remains Google’s decision |
| **7. CELIKOM integration** | BLOCKED pending approval | Only after complete standalone validation, independently connect with explicit compile/build flag and kill switch | Remove all ad module wiring and get byte-for-byte functionally equivalent CELIKOM baseline; replacement engine unaffected |

## First action for Stage 1

1. Document how each ad class behaves in current Yandex Music, comparing Plus and non-Plus **only through authorized test access**.
2. Separate claims from real observations. Do not assume removing HTML removes sound.
3. Verify which Chrome MV3 APIs are available and whether safe request filtering can avoid music/Range requests.
4. Record third-party source licenses, especially projects that do not declare one.
5. Propose measurable acceptance cases before writing blocker code.
6. Stop on blockers rather than expanding scope into unofficial desktop/app modification or bypassing paid access.

## Decision rules

- No production delivery of a partial banner-only solution masquerading as complete.
- When a platform/policy/technical issue prevents full Chrome functionality, give the owner a candid NO-GO recommendation and retain research assets.
- No updates to root CELIKOM docs or PRs during research.
- Next checkpoint: "Stage 1 GO/NO-GO" and dated evidence, saved in ad-protection/.
