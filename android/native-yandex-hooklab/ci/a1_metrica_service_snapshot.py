"""Finite read-only Android13 process/service snapshot; no raw guest data exported."""
from __future__ import annotations

ORIGINAL="ru.yandex.music"
CLONE="pro.celikom.yandex.nativeclonelab"

def classify_metrica_service_snapshot(ps_text:str, services_text:str, package:str,
                                     *, ps_ok:bool, services_ok:bool)->dict:
    if package not in (ORIGINAL,CLONE):
        raise ValueError("INVALID_PRIVATE_APP_NAMESPACE")
    own=[]
    if ps_ok:
        for line in ps_text.splitlines()[:2500]:
            words=line.split()
            if not words: continue
            name=words[-1]
            if name==package or name.startswith(package+":"):
                own.append(name)
    metrica_aux=sum(name.startswith(package+":") and
        "metrica" in name[len(package)+1:].lower() for name in own)
    # An observed service record is not proof of SDK readiness.
    service_candidate=False
    if services_ok:
        service_candidate=any(
            package in line and "metrica" in line.lower()
            for line in services_text.splitlines()[:8000])
    return {
        "process_sample_available":bool(ps_ok),
        "service_sample_available":bool(services_ok),
        "own_process_count_bounded":min(len(own),16) if ps_ok else None,
        "metrica_aux_process_count_bounded":min(metrica_aux,8) if ps_ok else None,
        "metrica_service_record_line_candidate":service_candidate if services_ok else None,
        "raw_process_or_service_data_disclosed":False,
    }
