"""Offline diagnostic decoder for an authenticated Ynison state frame.

No networking, credentials, registration, transport commands or audio operations.
Account authorization and physical cross-check are deliberately separate gates.
Schema reference: MarshalX/yandex-music-api @ 9ca132e5c18a72aab779c1fc68c169380a9357d0.
"""
import re


def field(value, camel, snake, default=None):
    if not isinstance(value, dict):
        return default
    return value.get(camel, value.get(snake, default))


def observe(frame, target_device_id, received_at_ms, now_ms):
    result = {"mode": "ynison_identity_diagnostic_only", "exact_track_id_verified": False,
              "replacement_started": False}

    def reject(reason):
        return dict(result, status=reason)

    if not isinstance(frame, dict):
        return reject("invalid_frame")
    if not target_device_id:
        return reject("target_device_unbound")
    if not 0 <= now_ms - received_at_ms <= 5000:
        return reject("observation_stale")
    active = field(frame, "activeDeviceIdOptional", "active_device_id_optional")
    if active != target_device_id:
        return reject("different_active_device")
    devices = frame.get("devices", [])
    if not isinstance(devices, list) or len(devices) > 100:
        return reject("invalid_devices")
    matches = [d for d in devices if isinstance(d, dict) and
               field(d.get("info"), "deviceId", "device_id") == target_device_id]
    if len(matches) != 1 or field(matches[0], "isOffline", "is_offline", False):
        return reject("target_device_unavailable")
    state = field(frame, "playerState", "player_state", {})
    if field(state, "playerQueueInjectOptional", "player_queue_inject_optional"):
        return reject("injected_content_active")
    queue = field(state, "playerQueue", "player_queue", {})
    index = field(queue, "currentPlayableIndex", "current_playable_index")
    rows = field(queue, "playableList", "playable_list", [])
    if type(index) is not int or not isinstance(rows, list) or not 0 <= index < len(rows) <= 5000:
        return reject("no_current_item")
    item = rows[index]
    kind = field(item, "playableType", "playable_type")
    if type(kind) not in (int, str) or kind not in (1, "TRACK"):
        return reject("not_catalog_track")
    identity = field(item, "playableId", "playable_id")
    if not isinstance(identity, str) or not re.fullmatch(r"[1-9][0-9]{0,23}", identity):
        return reject("invalid_track_id")
    result.update(status="server_track_id_candidate_unverified", candidate_track_id=identity,
                  target_device_matched=True, received_at_ms=received_at_ms)
    album = field(item, "albumIdOptional", "album_id_optional")
    if isinstance(album, str) and re.fullmatch(r"[1-9][0-9]{0,23}", album):
        result["candidate_album_id"] = album
    status = state.get("status", {}) if isinstance(state, dict) else {}
    paused = field(status, "paused", "paused")
    if type(paused) is bool:
        result["paused"] = paused
    progress = field(status, "progressMs", "progress_ms")
    if isinstance(progress, str) and progress.isdecimal() and len(progress) <= 12:
        progress = int(progress)
    if type(progress) is int and 0 <= progress <= 86400000:
        result["position_ms"] = progress
    return result
