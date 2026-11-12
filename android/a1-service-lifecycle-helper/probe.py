#!/usr/bin/env python3
"""B-only, bounded Android13 ActivityManager lifecycle A/B observer.

Read-only host witness. Reuses A's unchanged verified original-first runner;
never hooks vendor callbacks, changes SDK results or suppresses Android fatals.
Only finite counters/enums cross the disposable native guest boundary.
"""
from __future__ import annotations
import collections
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

HELPER_BRANCH = "experiment/android-a1-helper-service-lifecycle-arm13-20261112"
STOCK = "ru.yandex.music"
CLONE = "pro.celikom.yandex.nativeclonelab"
CONTAINER = "celikom-native-arm-android13"
ROOT = Path(__file__).resolve().parents[1] / "native-yandex-hooklab"
EVENTS = (
    "am_proc_start", "am_proc_bound", "am_proc_died", "am_create_service",
    "am_destroy_service", "am_bind_service", "am_service_bound",
    "am_service_args", "am_schedule_service_restart", "am_service_crashed_too_much",
)
EVENT_RE = re.compile(r"\\b(" + "|".join(EVENTS) + r")\\b")
RECORD_RE = re.compile(r"ServiceRecord\\{[^\\n]{0,300}", re.I)
ATTR_RE = re.compile(r'^\\s*A:\\s*android:(name|process|exported|enabled)[^=]*=\\s*(?:"([^"]*)"|\\(type[^)]*\\)([^\\n]*))')
MAX_RAW = 1_500_000


def run_guest(*argv: str, timeout: int = 15) -> tuple[bool, str]:
    try:
        out = subprocess.run(["docker", "exec", CONTAINER, *argv],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             text=True, errors="replace", timeout=timeout, check=False)
        return out.returncode == 0, out.stdout[:MAX_RAW]
    except (OSError, subprocess.TimeoutExpired):
        return False, ""


def manifest_components(xmltree: str, package: str) -> dict:
    """AAPT binary manifest tree; labels only, never original component names."""
    services = []
    active = None
    for line in xmltree.splitlines()[:30_000]:
        indent = len(line) - len(line.lstrip())
        stripped = line.lstrip()
        if re.match(r"E: service(?:\\s|$)", stripped):
            if active is not None:
                services.append(active)
            active = {"indent": indent, "name": "", "process": "", "exported": "UNKNOWN", "enabled": "UNKNOWN"}
            continue
        if active is not None and stripped.startswith("E: ") and indent <= active["indent"]:
            services.append(active)
            active = None
        if active is None or indent <= active["indent"]:
            continue
        match = ATTR_RE.match(line)
        if match:
            key, value, typed = match.groups()
            if value is None:
                value = "true" if "0xffffffff" in typed else "false" if "0x0" in typed else "UNKNOWN"
            active[key] = value
    if active is not None:
        services.append(active)
    metrica = [s for s in services if "metrica" in (s["name"] + " " + s["process"]).lower()]
    def proc_kind(raw: str) -> str:
        if not raw:
            return "DEFAULT"
        if raw.startswith(":"):
            return "PRIVATE"
        if raw == package or raw.startswith(package + ":"):
            return "OWN"
        if raw == STOCK or raw.startswith(STOCK + ":"):
            return "STOCK_EXPLICIT"
        if raw == CLONE or raw.startswith(CLONE + ":"):
            return "CLONE_EXPLICIT"
        return "OTHER_EXPLICIT"
    return {
        "all_service_count": min(len(services), 2000),
        "metrica_service_count": min(len(metrica), 80),
        "metrica_process_kinds": dict(collections.Counter(proc_kind(s["process"]) for s in metrica)),
        "metrica_exported": dict(collections.Counter(s["exported"] for s in metrica)),
        "metrica_enabled": dict(collections.Counter(s["enabled"] for s in metrica)),
        "_names": frozenset(s["name"] for s in metrica),
    }


def process_snapshot(ps: str, package: str) -> tuple[int, int, int]:
    main = aux = metrica = 0
    for line in ps.splitlines()[:2500]:
        fields = line.split()
        if not fields:
            continue
        name = fields[-1]
        main += int(name == package)
        aux += int(name.startswith(package + ":"))
        metrica += int(name.startswith(package + ":") and "metrica" in name.lower())
    return min(main, 3), min(aux, 16), min(metrica, 8)


def service_snapshot(dump: str, package: str) -> tuple[int, int, int]:
    records = 0
    running = 0
    bound = 0
    for match in RECORD_RE.finditer(dump[:MAX_RAW]):
        line = match.group(0)
        if package not in line or "metrica" not in line.lower():
            continue
        records += 1
        end = dump.find("ServiceRecord{", match.end(), min(len(dump), match.end() + 5000))
        segment = dump[match.end(): end if end >= 0 else min(len(dump), match.end() + 5000)]
        running += int(bool(re.search(r"\\bapp=ProcessRecord\\{", segment)))
        bound += int(bool(re.search(r"\\b(?:Connections:|Bindings:|connectionCount=)", segment)))
    return min(records, 16), min(running, 16), min(bound, 16)


def event_snapshot(log: str, package: str) -> dict:
    counts = collections.Counter()
    ordered = []
    for line in log.splitlines()[-20000:]:
        if package not in line:
            continue
        event = EVENT_RE.search(line)
        if not event:
            continue
        kind = event.group(1)
        target = "METRICA" if "metrica" in line.lower() else "APP_OTHER"
        key = kind + "_" + target
        counts[key] += 1
        if len(ordered) < 48:
            ordered.append(key)
    return {"event_rows": min(sum(counts.values()), 500),
            "event_counts": dict(sorted((k, min(v, 100)) for k,v in counts.items())),
            "event_order_first_48": ordered,
            "matching_events_observed": bool(counts)}


class Sampler:
    def __init__(self, phase: str, package: str):
        self.phase, self.package = phase, package
        self.stop = threading.Event()
        self.summary = collections.Counter()
        self.samples = 0
        self.errors = collections.Counter()
        self.thread = threading.Thread(target=self.sample_loop, daemon=True)

    def sample_loop(self):
        # AOSP event log retains transient events; samples also test actual live PID.
        for _ in range(34):
            if self.stop.is_set():
                break
            ok, ps = run_guest("ps", "-A", timeout=12)
            if ok:
                main, aux, metrica = process_snapshot(ps, self.package)
                self.summary["main_seen"] |= int(main > 0)
                self.summary["aux_seen"] |= int(aux > 0)
                self.summary["metrica_aux_seen"] |= int(metrica > 0)
                self.summary["peak_aux"] = max(self.summary["peak_aux"], aux)
            else:
                self.errors["ps"] += 1
            ok, dump = run_guest("dumpsys", "activity", "services", self.package, timeout=16)
            if ok:
                svc, active, bound = service_snapshot(dump, self.package)
                self.summary["service_record_seen"] |= int(svc > 0)
                self.summary["service_running_record_seen"] |= int(active > 0)
                self.summary["service_bind_record_seen"] |= int(bound > 0)
            else:
                self.errors["services"] += 1
            self.samples += 1
            if self.stop.wait(1.8):
                break

    def start(self):
        self.thread.start()

    def finish(self) -> dict:
        self.stop.set()
        self.thread.join(timeout=20)
        ok, events = run_guest("logcat", "-d", "-b", "events", "-v", "tag", timeout=25)
        return {
            "phase": self.phase,
            "sampling_rounds": self.samples,
            "sampling_errors_bounded": {k: min(v, 34) for k,v in self.errors.items()},
            "host": {k: bool(self.summary[k]) if k.endswith("_seen") else self.summary[k]
                     for k in ("main_seen", "aux_seen", "metrica_aux_seen",
                               "peak_aux", "service_record_seen",
                               "service_running_record_seen", "service_bind_record_seen")},
            "android_events_available": ok,
            "events": event_snapshot(events, self.package) if ok else None,
            "service_oncreate_java_callback_directly_observed": False,
            "raw_guest_data_exported": False,
        }


def main() -> int:
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("GITHUB_REPOSITORY") != "manufact-test/nomusic"
            or os.environ.get("GITHUB_REF_NAME") != HELPER_BRANCH
            or os.environ.get("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1"):
        print('{"helper_verdict":"DISPOSABLE_HELPER_BRANCH_ONLY"}')
        return 2
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--xapk", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    import ci.owner_2025_lspatch2_namespaced_clone_arm13 as lead

    # The ONLY altered runtime guard is B's isolated branch identity.
    # The original runner, module, original APK, SDK methods and fatal path stay intact.
    lead.BRANCH = HELPER_BRANCH
    results: dict = {}
    original_merge = lead.merge_publisher_input_lspatch_clone_splits
    def capture_manifests(renamed, editor, work, key):
        single = original_merge(renamed, editor, work, key)
        stock_bases = [p for p in (work / "trusted-source-splits").glob("*.apk")
                       if not lead.apk_name(p).get("split", "")]
        if len(stock_bases) == 1:
            def capture(path, package):
                cmd = lead.cmd(["aapt", "dump", "xmltree", str(path), "AndroidManifest.xml"], timeout=50)
                return manifest_components(cmd.stdout if cmd.returncode == 0 else "", package)
            original = capture(stock_bases[0], STOCK)
            clone = capture(single, CLONE)
            results["manifest"] = {
                "stock": {k:v for k,v in original.items() if not k.startswith("_")},
                "clone": {k:v for k,v in clone.items() if not k.startswith("_")},
                "metrica_class_names_match_in_memory": original["_names"] == clone["_names"],
                "binary_manifest_read_succeeded": bool(original["all_service_count"] and clone["all_service_count"]),
            }
        else:
            results["manifest"] = {"binary_manifest_read_succeeded": False}
        return single
    lead.merge_publisher_input_lspatch_clone_splits = capture_manifests

    stock_launch = lead.publisher_control.launch_main
    def clear_and_launch(*args, **kwargs):
        run_guest("logcat", "-c", timeout=15)
        return stock_launch(*args, **kwargs)
    lead.publisher_control.launch_main = clear_and_launch

    def wrap(phase, package, fn):
        def collect(*args, **kwargs):
            s = Sampler(phase, package)
            s.start()
            try:
                return fn(*args, **kwargs)
            finally:
                results[phase] = s.finish()
                print("HELPER_LIFECYCLE_PHASE " + json.dumps(results[phase], sort_keys=True), flush=True)
        return collect
    lead.publisher_control.observe = wrap("stock", STOCK, lead.publisher_control.observe)
    lead.observe_clone = wrap("clone", CLONE, lead.observe_clone)
    try:
        report = lead.run(args.xapk)
        results["original_runner_verdict"] = report.get("verdict", "UNKNOWN")
        results["native_stock_25_of_25"] = bool(report.get("publisher_stable_75s_before_clone"))
        results["native_clone_25_of_25"] = bool(report.get("native_clone_main_75s"))
        results["clone_fatal_suppression_observed"] = report.get("scoped_own_readonly_witness",{}).get("lab_only_metrica_fatal_suppression_observed")
        print("HELPER_LIFECYCLE_RESULT " + json.dumps(results, sort_keys=True), flush=True)
        print("ORIGINAL_RUNNER_RESULT " + json.dumps(report, sort_keys=True), flush=True)
        return 0 if results["native_stock_25_of_25"] and results["native_clone_25_of_25"] and not results["clone_fatal_suppression_observed"] else 1
    except Exception as e:
        # No private guest error text escapes the runner.
        print("HELPER_LIFECYCLE_ABORT " + json.dumps({"phase_names": sorted(results), "category":"RUNNER_EXCEPTION", "raw_data_exported":False}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
