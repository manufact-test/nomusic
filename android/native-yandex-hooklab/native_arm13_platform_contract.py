"""Read-only Android 13 PackageManager and system-denial differential.

No permission grants, identity changes, vendor modifications or raw telemetry
export. Observed permissions/denials alone never prove an EXIT_SELF(0) cause.
"""
from __future__ import annotations
import re
from clone_main_crash_buffer import CLONE, LOG

ORIGINAL = "ru.yandex.music"
PACKAGES = frozenset((CLONE, ORIGINAL))
FOCUS = "com.yandex.permission.READ_CREDENTIALS"
PERMISSION = re.compile(r"^[A-Za-z][A-Za-z0-9_.]{2,170}$")
GRANT = re.compile(r"^([A-Za-z][A-Za-z0-9_.]{2,170}):\s*granted=(true|false)\b", re.I)
USER = re.compile(r"^User\s+(\d{1,5}):")
SECTIONS = {"requested permissions": "requested",
            "install permissions": "install",
            "runtime permissions": "runtime"}
GROUPS = ("ANDROID", "YANDEX", "GOOGLE", "OTHER")
OS_TAGS = frozenset(("ActivityManager", "ActivityTaskManager", "PackageManager",
                     "PermissionManager", "PermissionManagerService",
                     "AppOps", "AppOpsService", "AppOpsManager", "ContextImpl"))
OS_DENIALS = (
    ("PERMISSION_DENIAL", re.compile(
        r"\bPermission Denial\b|\bpermission denied\b|"
        r"\bdenied(?: access)? to [\w. ]{0,60}permission\b", re.I)),
    ("COMPONENT_DENIAL", re.compile(
        r"\bnot exported\b|\bnot allowed to (?:start|bind|access)\b", re.I)),
    ("APP_OP_DENIAL", re.compile(
        r"\bapp.?op\b.{0,80}\b(?:deny|denied|reject|not allowed)\b", re.I)),
    ("SECURITY_EXCEPTION", re.compile(r"\bSecurityException\b")),
)
MAX_TEXT = 1_500_000


def _check(package: str):
    if package not in PACKAGES:
        raise ValueError("UNAPPROVED_PACKAGE")


def _group(permission: str) -> str:
    if permission.startswith(("com.yandex.", "ru.yandex.")):
        return "YANDEX"
    if permission.startswith("android.permission."):
        return "ANDROID"
    if permission.startswith("com.google."):
        return "GOOGLE"
    return "OTHER"


def _counts(names) -> dict:
    result = {x: 0 for x in GROUPS}
    for name in names:
        result[_group(name)] = min(500, result[_group(name)] + 1)
    return result


def _empty() -> dict:
    return {"available": False, "requested": set(), "install": {},
            "runtime": {}, "seen": set()}


def _parse(raw: str, package: str) -> dict:
    _check(package)
    data = _empty()
    if not isinstance(raw, str) or len(raw) > MAX_TEXT:
        return data
    # Anchor to the exact package record, not an arbitrary mention in a
    # package-owned permission or component. Only User 0 runtime grants count.
    head = re.search(r"(?m)^\s{2,}Package \[" + re.escape(package) + r"\]\s+\(", raw)
    if head is None:
        return data
    remainder = raw[head.end():]
    next_head = re.search(r"(?m)^\s{2,}Package \[[^\]\n]+\]\s+\(", remainder)
    if next_head:
        remainder = remainder[:next_head.start()]
    section, user_zero = "", False
    for line in remainder.splitlines()[:10000]:
        value = line.strip()
        match = USER.fullmatch(value)
        if match:
            user_zero = match.group(1) == "0"
            section = ""
            continue
        label = value.rstrip(":").lower()
        if value.endswith(":") and label in SECTIONS:
            candidate = SECTIONS[label]
            section = candidate if candidate != "runtime" or user_zero else ""
            if section:
                data["seen"].add(section)
            continue
        if value.endswith(":"):
            section = ""
            continue
        if section == "requested" and PERMISSION.fullmatch(value):
            data["requested"].add(value)
        elif section in ("install", "runtime"):
            match = GRANT.match(value)
            if match:
                data[section][match.group(1)] = match.group(2).lower() == "true"
    data["available"] = {"requested", "install"} <= data["seen"]
    return data if data["available"] else _empty()


def classify_installed_permission_state(raw: str, package: str) -> dict:
    record = _parse(raw, package)
    available = record["available"]
    focus_grant = record["install"].get(FOCUS)
    granted = lambda kind: [p for p, is_granted in record[kind].items() if is_granted]
    denied = lambda kind: [p for p, is_granted in record[kind].items() if not is_granted]
    return {
        "snapshot": "AVAILABLE" if available else "UNAVAILABLE",
        "requested_count_bounded": min(500, len(record["requested"])),
        "requested_groups": _counts(record["requested"]),
        "install_granted_groups": _counts(granted("install")),
        "install_denied_groups": _counts(denied("install")),
        "runtime_granted_groups": _counts(granted("runtime")),
        "runtime_denied_groups": _counts(denied("runtime")),
        "focus_credential_requested": available and FOCUS in record["requested"],
        "focus_credential_install_grant": (
            "NOT_OBSERVED" if not available else
            "GRANTED" if focus_grant is True else
            "DENIED" if focus_grant is False else "NOT_LISTED"),
        "raw_names_or_values_exposed": False,
    }


def compare_installed_permission_states(clone_raw: str, original_raw: str) -> dict:
    clone, original = _parse(clone_raw, CLONE), _parse(original_raw, ORIGINAL)
    available = clone["available"] and original["available"]
    shared = clone["requested"] & original["requested"] if available else set()
    original_held = {p for category in ("install", "runtime")
                     for p, granted in original[category].items() if granted}
    clone_held = {p for category in ("install", "runtime")
                  for p, granted in clone[category].items() if granted}
    missing = (shared & original_held) - clone_held
    not_listed = {p for p in missing if p not in clone["install"] and
                  p not in clone["runtime"]}
    return {
        "comparison": "AVAILABLE" if available else "INCONCLUSIVE",
        "shared_requested_count_bounded": min(500, len(shared)),
        "original_granted_clone_not_granted_shared_count_bounded":
            min(500, len(missing)),
        "clone_explicitly_denied_shared_count_bounded":
            min(500, len(missing - not_listed)),
        "clone_grant_not_listed_shared_count_bounded": min(500, len(not_listed)),
        "missing_grant_groups": _counts(missing),
        "missing_focus_credential_permission": FOCUS in missing,
        "raw_permission_names_exposed": False,
        "correlation_not_causation": True,
        "no_permission_grant_or_security_override": True,
    }


def _mentioned(message: str, package: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9_.])" + re.escape(package) +
                     r"(?![A-Za-z0-9_.:])", message) is not None


def classify_public_system_denials(raw: str, package: str) -> dict:
    """Count only exact-package public OS warnings; ambiguous rows discarded.

    System services log under their OWN PID, not the app MAIN PID; a package
    mention does not by itself prove which process triggered an event.
    """
    _check(package)
    counts = {label: 0 for label, _ in OS_DENIALS}
    ambiguous, examined = 0, 0
    if not isinstance(raw, str) or len(raw) > MAX_TEXT:
        raw = ""
    other = ORIGINAL if package == CLONE else CLONE
    for line in raw.splitlines()[-12000:]:
        match = LOG.match(line)
        if not match:
            continue
        _, severity, tag, message = match.groups()
        if severity not in ("W", "E", "F") or tag.strip() not in OS_TAGS:
            continue
        examined += 1
        if not _mentioned(message, package):
            continue
        if _mentioned(message, other):
            ambiguous += 1
            continue
        for label, expression in OS_DENIALS:
            if expression.search(message):
                counts[label] = min(100, counts[label] + 1)
                break
    return {
        "system_buffer_available": bool(raw.strip()),
        "scoped_platform_warning_error_lines_bounded": min(12000, examined),
        "exact_package_denial_categories": [k for k, n in counts.items() if n],
        "exact_package_denial_counts_bounded": counts,
        "ambiguous_two_package_lines_ignored_bounded": min(100, ambiguous),
        "raw_logs_or_package_data_exposed": False,
        "observed_denial_is_not_exit_cause": True,
    }
