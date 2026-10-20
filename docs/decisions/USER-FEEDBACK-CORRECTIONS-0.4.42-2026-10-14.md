# Owner review corrections — 0.4.42 (2026-10-14)

The owner authorized all gathered corrections after accepting grouped song demand
and existing-version proposal protection. Those accepted behaviors remain intact.

- Support account list has one total-ticket column and highlights accounts with
  open tickets. Inside accounts, both category labels have no counts; pending
  categories are highlighted and counts appear below the selected category.
  Ordinary email replies and song-report resolution are preserved.
- Local MP3 notice appears directly after the picker, before rights and submit.
  Incompatible notices scroll into view. Difference >5000ms in either direction
  disables submission, including direct form submission; selecting another file
  recalculates and unlocks. Exactly 5000ms remains warning-only. The separate
  1500ms playback limit is explained without publication/editor instructions.
- Server independently measures MP3 and rejects >5000ms before catalog writes,
  using existing stored Track duration when present, rechecked under row lock.
  API returns duration_mismatch; existing permissions and moderation unchanged.
- Duration alert count and default mismatch list include pending and active,
  approved replacements only. Rejected/disabled rows remain in explicit history.

## Owner-requested audio trim

Yandex Track 1944599, replacement 5, Зануда — Папиросы: original 200820ms,
old audio 242390ms. Contrary to the initial assumption, decoded inspection found
sound throughout the removed tail (peak 31451/32768); this was disclosed before
applying the explicitly requested exact endpoint. Full original and before/after
metadata are preserved in a private on-host backup; original AudioAsset retained.

Workflow 38618103286 SUCCESS: retained MP3 frames and decoded prefix samples are
identical without re-encoding. New duration 200829ms (9ms MP3-frame boundary error),
AudioAsset 28, replacement version 3, active approval retained. SHA-256
1d891d4e6b9f7ae8521dbc451ba12d1981102594eb335bba79a26e2438eb8f9d.
First two inspection attempts stopped before mutation on the silence assertion;
final authorized exact-endpoint trim separately guarded source hash/version.

## Validation

225 extension tests pass, including direct duration-block bypass attempt and
unlock after selecting a matching file. Lint, validation, configured API origin,
ZIP integrity and security gates pass. Private Chrome 38617424550 SUCCESS;
MySQL CI 38617432374 and 38617506164 SUCCESS; MariaDB 38617424456 SUCCESS.
ZIP SHA-256 b2f63404f665c207e8384564a28454a2ee8a0ed6e393770b9e263cb6e6a565dc.

Final CI 38618113737 SUCCESS and guarded deploy 38618103269 (attempt 2)
SUCCESS: active release 0.4.42-ea0d2a4e928867665e096f173823264948cd5e28.
Private environment/data preserved, 22 audio objects verified, isolated file and
MySQL restore PASS. Live read-only audit: 2 ordinary tickets retained, song
reports 0, simplified inbox PASS, actionable duration alerts 0, Papirosy 200829ms,
other two previously repaired active versions preserved. No real emails sent.
Earlier deploy stopped before SSH on stale branch guard; final initial attempt
and CI initial attempt hit external image-registry data limits before tests.
Unchanged retries passed. No guard or test was weakened for deployment.
Owner UI/audio acceptance remains pending. PR 6 remains open/unmerged; Issue 7 stays open.
