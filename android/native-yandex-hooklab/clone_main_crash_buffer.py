"""Private CI-only Android crash-buffer classifier for independent native clone.

Reads Android's CRASH log buffer *only* on a disposable emulator after an
unauthenticated cold start. Scopes every line to MAIN PIDs recorded in
ApplicationExitInfo. Returns a fixed vocabulary of boolean/enum signals;
never exports process IDs, class names, stack frames, messages, paths, URLs,
tokens, or raw logcat lines. Does not install, run, patch or read any app.
"""
from __future__ import annotations

import re

CLONE = "pro.celikom.yandex.nativeclonelab"
LOG = re.compile(
    r"^\s*\d\d-\d\d\s+\d\d:\d\d:\d\d\.\d+\s+"
    r"(\d{1,8})\s+\d+\s+([A-Z])\s+([^:]{1,48}):\s*(.*)$")
EXIT_BLOCK = re.compile(
    r"(?im)(?=^\s*(?:ApplicationExitInfo\s*#?\d+|#\d+:\s*ApplicationExitInfo))")
ALLOWED_TARGET_PACKAGES = frozenset(("pro.celikom.yandex.nativeclonelab", "ru.yandex.music"))
def _target_guard(value: str) -> None:
    if value not in ALLOWED_TARGET_PACKAGES:
        raise ValueError("UNSUPPORTED_OFFLINE_CRASH_TARGET")


ALLOWED_CATEGORIES = (
    "NATIVE_LINK", "NATIVE_SIGNAL", "CLASS_RESOLUTION", "DEX_VERIFICATION", "PERMISSION",
    "RESOURCE", "APPLICATION_STATE", "OTHER_JAVA", "NOT_OBSERVED")


def main_exit_pids(exit_dump: str, target_package: str = CLONE) -> set[int]:
    _target_guard(target_package)
    chunks = EXIT_BLOCK.split(exit_dump[:250000])
    if len(chunks) == 1:
        chunks = exit_dump[:250000].splitlines()
    values: set[int] = set()
    for chunk in chunks[:100]:
        process = re.search(
            r"\b(?:processName|process|process name)\s*[=:]\s*"
            r"([A-Za-z0-9_.:]+)", chunk, re.I)
        if process is None or process.group(1) != target_package:
            continue
        match = re.search(r"\bpid\s*[=:]\s*(\d{1,8})\b", chunk, re.I)
        if match is not None:
            pid = int(match.group(1))
            if 1 <= pid <= 99999999:
                values.add(pid)
    return values



def _native_link_failure_mode(log_text: str) -> str:
    """Fixed, privacy-safe linker diagnostics. Never return an error message."""
    patterns = (
        ("NAMESPACE_DENIED", r"not accessible for the namespace|not permitted in linker namespace|namespace.*(?:inaccessible|denied)"),
        ("DEP_MISSING", r"(?:needed by|referenced by|DT_NEEDED).*?(?:not found|missing)|library.{0,150}[.]so.{0,30}not found"),
        ("LIBRARY_NOT_FOUND", r"liblspatch[.]so.{0,80}not found|no such file or directory|couldn.t find|cannot find"),
        ("SYMBOL_UNRESOLVED", r"cannot locate symbol|undefined symbol|symbol lookup error"),
        ("ELF_ARCH_INVALID", r"wrong ELF class|instead of (?:32|64)-bit|e_machine|unexpected ELF|ELFCLASS|is for EM_|instead of EM_"),
        ("ELF_INVALID", r"bad ELF|invalid ELF|not an ELF|ELF header|ELF load command"),
        ("ZIP_ENTRY_INVALID", r"zip entry|zip archive|zip file|not uncompressed|compressed entry|invalid zip"),
        ("PAGE_OR_MMAP", r"mmap failed|couldn't map|could not map|page aligned|not page-aligned|invalid offset|segment.*align"),
        ("LIBRARY_SECURITY_DENIED", r"permission denied|access denied|avc: denied|SELinux"),
        ("RELOCATION_FAILURE", r"relocation|unsupported relocation|relocating"),
        ("JNI_INIT_FAILURE", r"JNI_OnLoad|init_array|DT_INIT"),
    )
    for label, pattern in patterns:
        if re.search(pattern, log_text, re.I | re.S):
            return label
    return "UNKNOWN_DLOPEN" if re.search(r"dlopen failed|UnsatisfiedLinkError", log_text, re.I) else "NOT_OBSERVED"


def _native_link_path_family(log_text: str) -> str:
    """Classify loading origin without exposing a path or package private data."""
    if re.search(r"\.apk!/assets/lspatch/so/", log_text, re.I):
        return "ZIP_ASSET_LOADER"
    if re.search(r"\.apk!/lib/", log_text, re.I):
        return "ZIP_LIB"
    if re.search(r"/(?:lib|lib64)/liblspatch\.so", log_text, re.I):
        return "EXTRACTED_LIB"
    if re.search(r"liblspatch\.so", log_text, re.I):
        return "UNSPECIFIED_LSPATCH_PATH"
    return "NOT_OBSERVED"


# Only static English diagnostic terms are allowed to leave the ephemeral CI.
# Never expose arbitrary dlerror fragments, paths, usernames or filenames.
LINKER_TERMS = frozenset((
    "access", "address", "aligned", "alignment", "allow", "already", "and",
    "android", "archive", "available", "bad", "because", "blocked", "cannot",
    "check", "class", "code", "compressed", "corrupt", "could", "data",
    "denied", "dependency", "dlopen", "dynamic", "elf", "entry", "error",
    "expected", "failed", "file", "files", "find", "for", "found", "from",
    "has", "have", "header", "in", "incompatible", "invalid", "isa", "is",
    "library", "libraries", "linker", "load", "loaded", "loading",
    "machine", "map", "mmap", "missing", "name", "native", "needed",
    "namespace", "no", "not", "of", "offset", "on", "open", "opening",
    "or", "page", "path", "permission", "relocation", "required",
    "requires", "section", "segment", "shared", "size", "so", "symbol",
    "system", "the", "to", "too", "unable", "undefined", "unexpected",
    "unknown", "unsupported", "using", "version", "was", "which",
    "with", "without", "wrong", "zip", "read", "phdr", "program",
    "memory", "reserved", "commit", "overlap", "overlapping",
))


def _dlopen_allowlisted_terms(messages: list[str]) -> list[str]:
    """Finite vocabulary: neither arbitrary substrings nor dynamic errors."""
    ordered = []
    for message in messages:
        match = re.search(r"dlopen failed:(.{0,1800})", message, re.I)
        if not match:
            continue
        for raw in re.findall(r"[A-Za-z]{2,30}", match.group(1)):
            word = raw.lower()
            if word in LINKER_TERMS and word not in ordered:
                ordered.append(word)
                if len(ordered) >= 25:
                    return ordered
    return ordered



def _elf_machine_mismatch(log_text: str) -> dict:
    """Bionic EM_MACHINE mismatch pair only; never an ELF path or exception."""
    match = re.search(
        r"is for\s+(EM_[A-Z0-9_]+)\s*\(\d+\)\s+instead of\s+(EM_[A-Z0-9_]+)\s*\(\d+\)",
        log_text, re.I)
    allowed = {"EM_386", "EM_ARM", "EM_AARCH64", "EM_X86_64"}
    if match is None:
        return {"seen": False, "actual": "UNKNOWN", "expected": "UNKNOWN"}
    actual, expected = match.group(1).upper(), match.group(2).upper()
    if actual not in allowed or expected not in allowed:
        return {"seen": False, "actual": "UNKNOWN", "expected": "UNKNOWN"}
    return {"seen": True, "actual": actual, "expected": expected}



def _native_backtrace_group(message: str) -> str:
    """Never expose raw PCs, paths, symbols or process data."""
    if re.search(r"(?:^|[/\s])liblspatch[.]so\b", message, re.I):
        return "LSPATCH"
    if re.search(r"lib(?:houdini|ndk_translation|nativebridge)[\w.]*[.]so", message, re.I):
        return "NATIVE_BRIDGE"
    if re.search(r"(?:^|[/\s])libart[.]so\b", message, re.I):
        return "LIBART"
    if re.search(r"(?:^|[/\s])libc[.]so\b", message, re.I):
        return "LIBC"
    if re.search(r"(?:^|[/\s])(?:linker|linker64)(?:\s|$)", message, re.I):
        return "LINKER"
    return "OTHER"


def classify_main_native_crash(exit_dump: str, crash_buffer: str, target_package: str = CLONE) -> dict:
    _target_guard(target_package)
    """Only owner MAIN PID and debuggerd header explicitly naming that PID.

    Tombstone backtraces are usually emitted by debuggerd, NOT by the
    crashing app PID. Scope DEBUG frames using its public victim header,
    and never return raw paths, stack traces, addresses, or arbitrary names.
    """
    victims = main_exit_pids(exit_dump, target_package)
    signal = "NOT_OBSERVED"
    reporters: set[int] = set()
    frames: list[str] = []
    header_seen = False
    for line in crash_buffer.splitlines()[-10000:]:
        parsed = LOG.match(line)
        if parsed is None:
            continue
        reporter_pid, severity, tag, message = parsed.groups()
        reporter_pid = int(reporter_pid)
        tag = tag.strip()
        if reporter_pid in victims and tag == "libc":
            hit = re.search(r"\bFatal signal\s+\d+\s+\((SIG[A-Z]+)\)", message)
            if hit and hit.group(1) in (
                    "SIGSEGV", "SIGABRT", "SIGBUS", "SIGILL", "SIGTRAP"):
                signal = hit.group(1)
        if tag != "DEBUG" or severity not in ("E", "F", "W"):
            continue
        if re.search(r"\bpid:\s*\d+\s*,\s*tid:", message):
            reporters.discard(reporter_pid)
            hit = re.search(r"\bpid:\s*(\d{1,8})\s*,\s*tid:", message)
            if hit and int(hit.group(1)) in victims and (
                    ">>> " + target_package + " <<<") in message:
                reporters.add(reporter_pid)
                header_seen = True
            continue
        if reporter_pid not in reporters:
            continue
        if len(frames) < 32 and re.match(r"\s*#\d{2}\s+pc\s+", message):
            frames.append(_native_backtrace_group(message))
    return {
        "native_main_signal": signal,
        "main_tombstone_header_matched": header_seen,
        "native_backtrace_frame_groups": frames[:12],
        "native_backtrace_first_frame_group": frames[0] if frames else "NOT_OBSERVED",
        "native_backtrace_frame_count_bounded": min(len(frames), 32),
        "raw_native_crash_exposed": False,
    }


JAVA_FRAME_FAMILY = (
    ("android.", "ANDROID_FRAMEWORK"),
    ("com.android.", "ANDROID_FRAMEWORK"),
    ("dalvik.", "ANDROID_FRAMEWORK"),
    ("java.", "JAVA_RUNTIME"),
    ("javax.", "JAVA_RUNTIME"),
    ("libcore.", "JAVA_RUNTIME"),
    ("sun.", "JAVA_RUNTIME"),
    ("androidx.", "ANDROIDX"),
    ("kotlin.", "KOTLIN"),
    ("kotlinx.", "KOTLIN"),
    ("com.google.android.gms.", "GOOGLE_SDK"),
    ("com.google.firebase.", "GOOGLE_SDK"),
    ("ru.yandex.", "YANDEX_APP"),
    ("com.yandex.", "YANDEX_APP"),
    ("pro.celikom.", "CELIKOM_APP"),
)
JAVA_ROOT_EXCEPTIONS = (
    ("ILLEGAL_STATE", "IllegalStateException"),
    ("NULL_POINTER", "NullPointerException"),
    ("ILLEGAL_ARGUMENT", "IllegalArgumentException"),
    ("SECURITY_EXCEPTION", "SecurityException"),
    ("RUNTIME_EXCEPTION", "RuntimeException"),
    ("UNSATISFIED_LINK", "UnsatisfiedLinkError"),
    ("CLASS_NOT_FOUND", "ClassNotFoundException"),
    ("NO_CLASS_DEF", "NoClassDefFoundError"),
    ("RESOURCE_NOT_FOUND", "NotFoundException"),
    ("UNKNOWN_JAVA_EXCEPTION", "Exception"),
)
JAVA_ALLOWED_FRAME_FAMILIES = frozenset(
    ("ANDROID_FRAMEWORK", "JAVA_RUNTIME", "ANDROIDX", "KOTLIN",
     "GOOGLE_SDK", "YANDEX_APP", "CELIKOM_APP",
     "OTHER_APP_OR_LIBRARY", "NOT_OBSERVED"))
JAVA_ALLOWED_THROWABLES = frozenset(x[0] for x in JAVA_ROOT_EXCEPTIONS) | {"NOT_OBSERVED"}

def _java_throwable_label(message: str) -> str:
    """Only output enum names. Never a vendor type, method or error text."""
    for label, literal in JAVA_ROOT_EXCEPTIONS:
        if re.search(r"(?<![A-Za-z0-9_$])" + re.escape(literal) + r"\b", message):
            return label
    return "NOT_OBSERVED"


def _java_frame_family(line: str) -> str:
    match = re.match(r"^\s*at\s+([A-Za-z_$][A-Za-z0-9_.$-]*)\(", line)
    if not match:
        return "NOT_OBSERVED"
    frame = match.group(1).lower()
    for prefix, label in JAVA_FRAME_FAMILY:
        if frame.startswith(prefix):
            return label
    return "OTHER_APP_OR_LIBRARY"


JAVA_LIFECYCLE_MARKERS = (
    ("APPLICATION_ON_CREATE", r"\bat android[.]app[.]Instrumentation[.]callApplicationOnCreate[(]"),
    ("APPLICATION_BIND", r"\bat android[.]app[.]ActivityThread[.]handleBindApplication[(]"),
    ("ACTIVITY_CREATE", r"\bat android[.]app[.]ActivityThread[.]performLaunchActivity[(]"),
    ("ACTIVITY_RESUME", r"\bat android[.]app[.]ActivityThread[.]performResumeActivity[(]"),
    ("CONTENT_PROVIDER_INSTALL", r"\bat android[.]app[.]ActivityThread[.]installProvider[(]"),
    ("APP_COMPONENT_FACTORY", r"\bat android[.]app[.]AppComponentFactory[.]instantiate"),
    ("MAIN_EVENT_LOOP", r"\bat android[.]os[.]Looper[.]loop[(]"),
)
JAVA_MESSAGE_HINTS = (
    ("TRUST_OR_PACKAGE", r"\b(?:signature|signing|certificate|certification|trusted|untrusted|integrity|installer)\b"),
    ("IDENTITY_OR_CONTEXT", r"\b(?:package|packageName|context|applicationId|uid|userId)\b"),
    ("SERVICE_OR_PROVIDER", r"\b(?:provider|service|binder|contentresolver|content provider)\b"),
    ("STARTUP_ORDER", r"\b(?:initializ(?:ed|ation|ing)|not initialized|already registered|not ready)\b"),
    ("FEATURE_OR_CONFIG", r"\b(?:feature|configuration|config|flag|setting|option)\b"),
    ("DEVICE_OR_PLATFORM", r"\b(?:unsupported|android version|emulator|device not|android api)\b"),
    ("ACCOUNT_OR_SESSION", r"\b(?:account|passport|session|login|authentication)\b"),
    ("STORAGE_OR_DATABASE", r"\b(?:database|sqlite|storage|preferences)\b"),
    ("NETWORK_OR_TRANSPORT", r"\b(?:network|timeout|connection|host|dns)\b"),
)
JAVA_HINT_LABELS = frozenset([a for a, _ in JAVA_MESSAGE_HINTS] + ["NONE"])
JAVA_LIFECYCLE_LABELS = frozenset([a for a, _ in JAVA_LIFECYCLE_MARKERS] + ["NOT_OBSERVED"])

def _java_lifecycle_origin(lines: list[str]) -> str:
    """Classify Android public framework frames, not vendor call sites."""
    for label, pattern in JAVA_LIFECYCLE_MARKERS:
        if any(re.search(pattern, ln) for ln in lines):
            return label
    return "NOT_OBSERVED"


def _java_message_category(lines: list[str]) -> str:
    """Only the first exception's message, not arbitrary vendor stack lines.

    Categories are weak signals, not proof of an integrity check.
    """
    first = False
    pieces: list[str] = []
    for ln in lines:
        if re.search(r"\bFATAL EXCEPTION:", ln):
            first = True
            continue
        if not first:
            continue
        if re.match(r"\s*(?:at\s+|Caused by:)", ln):
            break
        if re.match(r"\s*[\w.$]+(?:Exception|Error)(?:\s*:|$)", ln):
            parts = ln.split(":", 1)
            if len(parts) == 2:
                pieces.append(parts[1][:240])
        elif pieces and len(pieces) < 3 and len(ln) < 256:
            pieces.append(ln)
    message = " ".join(pieces)
    for label, pattern in JAVA_MESSAGE_HINTS:
        if re.search(pattern, message, re.I):
            return label
    return "NONE"


def _scoped_android_runtime_java_origin(lines: list[str]) -> dict:
    """Summarize AndroidRuntime MAIN stack without ever exporting stack names.

    The caller must already constrain the lines to exact MAIN PID and to the
    AndroidRuntime crash tag. Cannot infer the presence of an integrity check.
    """
    body = lines[:500]
    top_exception = "NOT_OBSERVED"
    root_exception = "NOT_OBSERVED"
    first_frame = "NOT_OBSERVED"
    last_cause_first_frame = "NOT_OBSERVED"
    cause_count = 0
    frame_count = 0
    waiting_for_cause_frame = False
    fatal_seen = False
    for line in body:
        if re.search(r"\bFATAL EXCEPTION:", line):
            fatal_seen = True
            continue
        if not fatal_seen:
            continue
        is_cause = re.match(r"\s*Caused by:\s*", line) is not None
        if is_cause:
            cause_count = min(cause_count + 1, 30)
            label = _java_throwable_label(line)
            root_exception = label
            last_cause_first_frame = "NOT_OBSERVED"
            waiting_for_cause_frame = True
        elif top_exception == "NOT_OBSERVED":
            # The first exception after FATAL header is usually on its own
            # AndroidRuntime line. Do not treat a stack-frame as exception.
            if not re.match(r"\s*(at\s+|\.\.\.\s*\d+\s+more)", line):
                top_exception = _java_throwable_label(line)
        fam = _java_frame_family(line)
        if fam != "NOT_OBSERVED":
            frame_count = min(frame_count + 1, 500)
            if first_frame == "NOT_OBSERVED":
                first_frame = fam
            if waiting_for_cause_frame:
                last_cause_first_frame = fam
                waiting_for_cause_frame = False
    if cause_count == 0:
        root_exception = top_exception
        last_cause_first_frame = first_frame
    startup_lifecycle = _java_lifecycle_origin(body)
    message_hint = _java_message_category(body)
    assert startup_lifecycle in JAVA_LIFECYCLE_LABELS
    assert message_hint in JAVA_HINT_LABELS
    assert first_frame in JAVA_ALLOWED_FRAME_FAMILIES
    assert last_cause_first_frame in JAVA_ALLOWED_FRAME_FAMILIES
    assert top_exception in JAVA_ALLOWED_THROWABLES
    assert root_exception in JAVA_ALLOWED_THROWABLES
    return {
        "java_fatal_seen_scoped": fatal_seen,
        "java_startup_lifecycle_enum": startup_lifecycle,
        "java_exception_message_hint_enum": message_hint,
        "java_top_exception_enum": top_exception,
        "java_last_cause_exception_enum": root_exception,
        "java_top_stack_family": first_frame,
        "java_last_cause_stack_family": last_cause_first_frame,
        "java_caused_by_count_bounded": cause_count,
        "java_stack_frame_count_bounded": frame_count,
        "java_stack_raw_exposed": False,
        "java_vendor_class_names_exposed": False,
    }


def classify_main_crash_buffer(exit_dump: str, crash_buffer: str, target_package: str = CLONE) -> dict:
    _target_guard(target_package)
    """Fixed category labels only, no raw process/exception data returned."""
    pids = main_exit_pids(exit_dump, target_package)
    parts = []
    android_runtime_lines = []
    for line in crash_buffer.splitlines()[-10000:]:
        event = LOG.match(line)
        if event is None or int(event.group(1)) not in pids:
            continue
        _, severity, tag, message = event.groups()
        if severity not in ("E", "F", "W") or tag.strip() not in (
                "AndroidRuntime", "libc", "DEBUG", "System.err"):
            continue
        if len(parts) < 500:
            parts.append(message[:2048])
        if tag.strip() == "AndroidRuntime" and len(android_runtime_lines) < 500:
            android_runtime_lines.append(message[:2048])
    text = "\n".join(parts)
    has = lambda pattern: re.search(pattern, text, re.I) is not None
    native_link = has(r"\b(?:UnsatisfiedLinkError|dlopen failed)\b")
    native_crash = classify_main_native_crash(exit_dump, crash_buffer, target_package)
    class_resolution = has(
        r"\b(?:ClassNotFoundException|NoClassDefFoundError|NoSuchMethodError)\b")
    dex_verification = has(r"\b(?:VerifyError|IncompatibleClassChangeError)\b")
    permissions = has(r"\b(?:SecurityException|Permission Denial)\b")
    resources = has(
        r"\b(?:InflateException|Resources\$NotFoundException)\b")
    app_state = has(r"\b(?:IllegalStateException|NullPointerException|IllegalArgumentException)\b")
    java_error = has(r"\b(?:Exception|Error)\b")
    category = (
        "NATIVE_LINK" if native_link else
        "NATIVE_SIGNAL" if native_crash["native_main_signal"] != "NOT_OBSERVED" else
        "CLASS_RESOLUTION" if class_resolution else
        "DEX_VERIFICATION" if dex_verification else
        "PERMISSION" if permissions else
        "RESOURCE" if resources else
        "APPLICATION_STATE" if app_state else
        "OTHER_JAVA" if java_error else "NOT_OBSERVED")
    assert category in ALLOWED_CATEGORIES
    # Fixed vocabulary of Java exception classes only. The message, stack,
    # proprietary type/field names, paths and all identifiers stay private.
    exception_patterns = {
        "ILLEGAL_STATE": r"\bIllegalStateException\b",
        "NULL_POINTER": r"\bNullPointerException\b",
        "ILLEGAL_ARGUMENT": r"\bIllegalArgumentException\b",
        "SECURITY_EXCEPTION": r"\bSecurityException\b",
        "RESOURCE_MISSING": r"\bResources\$NotFoundException\b",
        "CLASS_NOT_FOUND": r"\bClassNotFoundException\b",
        "LINK_ERROR": r"\bUnsatisfiedLinkError\b",
    }
    exception_subtypes = sorted(label for label, pattern in exception_patterns.items()
                                if re.search(pattern, text))
    return {
        **native_crash,
        **_scoped_android_runtime_java_origin(android_runtime_lines),
        "crash_main_pid_evidence_available": bool(pids),
        "crash_buffer_main_pid_lines_seen": bool(parts),
        "android_runtime_fatal_main_seen": has(r"FATAL EXCEPTION:"),
        "native_link_error_seen": native_link,
        "native_link_library_lspatch_named": has(r"liblspatch\.so"),
        "native_link_library_cpp_shared_named": has(r"libc\+\+_shared\.so"),
        "native_link_dlopen_failed": has(r"dlopen failed"),
        "native_link_failure_mode": _native_link_failure_mode(text),
        "native_link_machine_mismatch": _elf_machine_mismatch(text),
        "native_link_allowlisted_terms": _dlopen_allowlisted_terms(parts),
        "native_link_path_family": _native_link_path_family(text),
        "native_link_error_line_observed": bool([p for p in parts if re.search(r"dlopen failed|UnsatisfiedLinkError", p, re.I)]),
        "native_link_wrong_elf_class": has(
            r"wrong ELF class|32-bit instead of 64-bit|64-bit instead of 32-bit"),
        "native_link_missing_library_marker": has(
            r"\blibrary\b.{0,120}\bnot found\b|cannot locate"),
        "android_native_bridge_mentioned": has(
            r"native.bridge|NativeBridge|libhoudini|libndk_translation"),
        "lspatch_bootstrap_mentioned": has(
            r"org\.lsposed\.lspatch|LSPAppComponentFactoryStub"),
        "application_component_factory_failure": has(
            r"Unable to instantiate appComponentFactory"),
        "application_create_failure": has(
            r"Unable to (?:create|instantiate) application"),
        "activity_launch_failure": has(r"Unable to start activity"),
        "fatal_category": category,
        "fixed_java_exception_subtypes": exception_subtypes,
        "raw_crash_buffer_exposed": False,
        "process_identifiers_exposed": False,
        "exception_free_text_exposed": False,
    }


def classify_main_exit_status(exit_dump: str, target_package: str = CLONE) -> dict:
    _target_guard(target_package)
    """Safely classify Android 13 ApplicationExitInfo for *exact clone MAIN*.

    REASON_EXIT_SELF=1, CRASH=4, CRASH_NATIVE=5; any helper/other package
    cannot contribute. Process IDs, times, traces, free text never leave CI.
    A missing MAIN record MUST report NOT_OBSERVED, never EXIT_SELF.
    """
    blocks = EXIT_BLOCK.split(exit_dump[:250000])
    if len(blocks) == 1:
        blocks = exit_dump[:250000].splitlines()
    names = {
        1: "EXIT_SELF", 2: "SIGNALED", 3: "LOW_MEMORY",
        4: "JAVA_CRASH", 5: "NATIVE_CRASH", 6: "ANR",
        7: "INITIALIZATION_FAILURE", 8: "PERMISSION_CHANGE",
        9: "EXCESSIVE_RESOURCES", 12: "DEPENDENCY_DIED",
    }
    matched = []
    for block in blocks[:100]:
        proc = re.search(
            r"\b(?:processName|process|process name)\s*[=:]\s*"
            r"([A-Za-z0-9_.:]+)", block, re.I)
        if proc is None or proc.group(1) != target_package:
            continue
        reason = re.search(r"\breason\s*[=:]\s*(\d{1,2})\b", block, re.I)
        if reason is None:
            continue
        code = int(reason.group(1))
        status = re.search(r"\bstatus\s*[=:]\s*(-?\d{1,6})\b", block, re.I)
        status_num = int(status.group(1)) if status else None
        status_label = ("ZERO" if status_num == 0 else
                        "NONZERO" if status_num is not None else
                        "NOT_REPORTED")
        matched.append({"reason": names.get(code, "UNKNOWN"),
                        "status": status_label})
    if not matched:
        return {"exact_main_exit_record_seen": False,
                "latest_main_exit_reason": "NOT_OBSERVED",
                "latest_main_exit_status": "NOT_REPORTED",
                "main_exit_record_count_bounded": 0,
                "raw_exit_info_exposed": False}
    return {"exact_main_exit_record_seen": True,
            "latest_main_exit_reason": matched[0]["reason"],
            "latest_main_exit_status": matched[0]["status"],
            "main_exit_record_count_bounded": min(len(matched), 100),
            "raw_exit_info_exposed": False}
