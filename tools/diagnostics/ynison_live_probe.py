"""Bounded Ynison observer using an already authorized owner's Music token.

No OAuth client impersonation or credential extraction. Only the passive remote
registration frame is sent; no playback/queue/volume/active-device commands.
"""
import argparse
import asyncio
import getpass
import hashlib
import json
import logging
import os
import re
import time
import urllib.parse
import uuid

from ynison_identity import field, observe

REDIRECT = "wss://ynison.music.yandex.ru/redirector.YnisonRedirectService/GetRedirectToYnison"
STATE_PATH = "/ynison_state.YnisonStateService/PutYnisonState"


def device_hash(identity):
    return hashlib.sha256(identity.encode()).hexdigest()[:16]


def state_uri(redirect):
    host = redirect.get("host", "")
    if not isinstance(host, str) or not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)*\.music\.yandex\.ru", host):
        raise ValueError("untrusted_redirect")
    ticket = field(redirect, "redirectTicket", "redirect_ticket")
    session = field(redirect, "sessionId", "session_id")
    if not isinstance(ticket, str) or not 1 <= len(ticket) <= 2048 or not session:
        raise ValueError("invalid_redirect")
    return "wss://" + host + STATE_PATH


def protocols(identity, redirect=None):
    info = {"Ynison-Device-Id": identity,
            "Ynison-Device-Info": json.dumps({"app_name": "CELIKOM identity diagnostic", "type": "1"})}
    if redirect:
        info["Ynison-Redirect-Ticket"] = field(redirect,"redirectTicket","redirect_ticket")
        info["Ynison-Session-Id"] = str(field(redirect,"sessionId","session_id"))
    return ["Bearer", "v2", urllib.parse.quote(json.dumps(info,separators=(",",":")), safe="")]


def registration(identity):
    return {"updateFullState": {
        "playerState": {"playerQueue": {"currentPlayableIndex": -1, "entityType": "VARIOUS",
            "options": {"repeatMode": "NONE"}, "version": {"deviceId": identity}},
            "status": {"paused": True, "playbackSpeed": 1,
                       "version": {"deviceId": identity, "timestampMs": "0"}}},
        "device": {"capabilities": {"canBePlayer": False,"canBeRemoteController": True},
            "info": {"deviceId": identity,"type": "WEB","title": "CELIKOM identity diagnostic",
                     "appName": "celikom-id-probe"},"volumeInfo": {"volume": 0}},
        "isCurrentlyActive": False}, "rid": uuid.uuid4().hex,
        "playerActionTimestampMs": "0", "activityInterceptionType": "DO_NOT_INTERCEPT_BY_DEFAULT"}


def summarize(frame, expected_hash, received_at_ms):
    active = field(frame,"activeDeviceIdOptional","active_device_id_optional","")
    active = active if isinstance(active,str) else ""
    target = active if active and device_hash(active)==expected_hash else ""
    report = observe(frame,target,received_at_ms,received_at_ms)
    report["active_device_hash"] = device_hash(active) if active else None
    devices = frame.get("devices",[])
    if isinstance(devices,list):
        report["device_candidates"] = []
        for row in devices[:30]:
            info = row.get("info",{}) if isinstance(row,dict) else {}
            identity = field(info,"deviceId","device_id","")
            if not isinstance(identity,str) or not identity:
                continue
            report["device_candidates"].append({"device_hash": device_hash(identity),
                "title": str(info.get("title",""))[:100], "type": info.get("type"),
                "active": identity==active,"offline": bool(field(row,"isOffline","is_offline",False))})
    return report


def strict_connector():
    from websockets.asyncio.client import connect
    class StrictConnect(connect):
        def process_redirect(self, error):
            # Only the authenticated, validated Ynison JSON redirect is accepted.
            # HTTP 30x must not forward Authorization to another origin.
            return error
    return StrictConnect


async def run(token, expected_hash, seconds, connect=None):
    if connect is None:
        connect = strict_connector()
    logger = logging.getLogger("celikom.ynison.private")
    logger.disabled = True
    kwargs = {"origin":"https://music.yandex.ru","additional_headers":{"Authorization":"OAuth " + token},
              "user_agent_header":"CELIKOM-ID-Probe/1","open_timeout":10,"close_timeout":2,
              "max_size":1048576,"max_queue":4,"logger":logger,"proxy":None}
    identity=uuid.uuid4().hex
    async with connect(REDIRECT,subprotocols=protocols(identity),**kwargs) as ws:
        redirect=json.loads(await asyncio.wait_for(ws.recv(),10))
    uri=state_uri(redirect)
    async with connect(uri,subprotocols=protocols(identity,redirect),ping_interval=15,ping_timeout=15,**kwargs) as ws:
        await ws.send(json.dumps(registration(identity)))
        deadline=time.monotonic()+seconds
        frames=0
        while time.monotonic()<deadline and frames<120:
            try:
                message=await asyncio.wait_for(ws.recv(),max(0.01,deadline-time.monotonic()))
            except asyncio.TimeoutError:
                break
            data=json.loads(message)
            if not isinstance(data,dict) or "error" in data:
                raise ValueError("server_error")
            if not field(data,"playerState","player_state"):
                continue
            frames+=1
            yield summarize(data,expected_hash,int(time.time()*1000))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device-hash",default="",help="Explicitly chosen playing phone from discovery report")
    parser.add_argument("--seconds",type=int,default=60)
    args=parser.parse_args()
    if not 5 <= args.seconds <= 120:
        parser.error("seconds must be 5..120")
    if args.device_hash and not re.fullmatch(r"[0-9a-f]{16}",args.device_hash):
        parser.error("device hash must have 16 hexadecimal characters")
    token=os.environ.get("CELIKOM_YANDEX_MUSIC_TOKEN")
    if not token:
        token=getpass.getpass("Authorized owner Music token (hidden, never saved): ")
    if not token or len(token)>8192 or any(c.isspace() for c in token):
        raise SystemExit("Invalid token input")
    async def collect():
        async for report in run(token,args.device_hash,args.seconds):
            print(json.dumps(report,ensure_ascii=False),flush=True)
        print(json.dumps({"status":"observation_finished","exact_track_id_verified":False}))
    try:
        asyncio.run(collect())
    except KeyboardInterrupt:
        pass
    except Exception as error:
        # Never print exception message: it may contain headers, redirect ticket or raw frame.
        print(json.dumps({"status":"connection_failed","error_type":type(error).__name__,
                          "exact_track_id_verified":False}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
