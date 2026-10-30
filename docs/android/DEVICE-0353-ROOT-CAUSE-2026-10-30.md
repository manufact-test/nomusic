# CELIKOM Android 0.3.53 HONOR field-log root cause and 0.3.54 correction

Source: user CELIKOM-combined-20261030-003008.txt. Device run_start 0.3.53 at 2026-10-30 00:28:35 +03.

## Proven defect

0.3.53 allowed a metadata probe within 1500ms, then rejected the actual decoded file whenever source-vs-file >500ms. This makes the probe ineffective.

Observed Yandex / server / decoded durations (ms):

- Крылья — SLIMUS, Ай-Q: 272700 / 272144 / 272118
- Биг сити лайф — Триагрутрика: 232450 / 231120 / 231096
- Метамир — Johnyboy: 286730 / 286067 / 286067
- Earlier: Всё пиздато — Зануда: 221930 / 223399 / 223399 (only metadata observed in 0.3.51)

## Android-only correction

Keep strict duration and decoder checks by default. For a strong album-constrained title/artist match or a user-confirmed candidate, a **measured** codec/outro discrepancy <=1500ms is accepted. The Yandex source clock remains authoritative. A shorter decoder finishes and the original is restored for the remaining bounded outro; the next source boundary always stops the retired decoder. Measured errors >1500ms or unverified identity remain unsupported. This is not an acoustic comparison or proof of identical song edition. End-to-end testing on HONOR is still mandatory.

## Other findings not claimed fixed

The 0.3.53 journal shows Монпасье source reset with 6938ms of displayed duration remaining and next alias about 160ms later. Do not continue a retired decoder for 7 seconds, which would risk overlap. Some seeks still exhibit short commanded-silence anomalies; hardware audio output is not measurable in the report. Fades were already 100ms source then 200ms replacement in 0.3.53.

Only `android/native-companion/**`, this document and the isolated Android workflow changed. Preserve 0.3.53 backups; no desktop/server/API/CMS/ad-protection edits and no keystore in Git.
