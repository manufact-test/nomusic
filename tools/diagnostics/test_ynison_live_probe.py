import json
import unittest
from ynison_live_probe import registration, state_uri, summarize, device_hash, run, strict_connector
from test_ynison_identity import frame


class TransportTests(unittest.IsolatedAsyncioTestCase):
    def test_http_redirects_are_not_followed(self):
        connector=strict_connector()("wss://ynison.music.yandex.ru",proxy=None)
        error=ValueError("test")
        self.assertIs(error,connector.process_redirect(error))

    def test_untrusted_redirects_never_receive_a_token(self):
        for host in ("evil.example", "music.yandex.ru.evil.example", "user@ynison.music.yandex.ru",
                     "ynison.music.yandex.ru:443", "ynison.music.yandex.ru/path", "127.0.0.1"):
            with self.assertRaises(ValueError):
                state_uri({"host":host,"redirectTicket":"ticket","sessionId":"1"})

    def test_registration_has_own_identity_and_cannot_take_over_player(self):
        request=registration("probe")
        full=request["updateFullState"]
        self.assertFalse(full["isCurrentlyActive"])
        self.assertFalse(full["device"]["capabilities"]["canBePlayer"])
        self.assertEqual("celikom-id-probe",full["device"]["info"]["appName"])
        self.assertEqual("DO_NOT_INTERCEPT_BY_DEFAULT",request["activityInterceptionType"])
        self.assertEqual("0",request["playerActionTimestampMs"])
        self.assertEqual({"updateFullState","rid","playerActionTimestampMs","activityInterceptionType"},set(request))

    async def test_handshake_observes_switches_without_sending_playback_commands(self):
        connections=[]
        class Socket:
            def __init__(self,uri,kwargs):
                self.uri=uri;self.kwargs=kwargs;self.sent=[]
                self.frames=([{ "host":"edge.music.yandex.ru","redirectTicket":"secret-ticket","sessionId":"1"}]
                    if not connections else [frame("38436680"),frame("48592132")])
                connections.append(self)
            async def __aenter__(self): return self
            async def __aexit__(self,*args): pass
            async def recv(self):
                if not self.frames: raise asyncio.TimeoutError()
                return json.dumps(self.frames.pop(0))
            async def send(self,message): self.sent.append(json.loads(message))
        import asyncio
        reports=[x async for x in run("owner-secret-token",device_hash("phone"),5,
                    connect=lambda uri,**kwargs: Socket(uri,kwargs))]
        self.assertEqual(["38436680","48592132"],[x["candidate_track_id"] for x in reports])
        self.assertEqual([],connections[0].sent)
        self.assertEqual(1,len(connections[1].sent))
        self.assertNotIn("owner-secret-token",str(reports));self.assertNotIn("secret-ticket",str(reports))
        self.assertNotIn("secret",str(reports))
        self.assertFalse(reports[-1]["replacement_started"])
        self.assertFalse(reports[-1]["exact_track_id_verified"])

    def test_device_must_be_chosen_and_raw_ids_are_not_exported(self):
        report=summarize(frame(),"",0)
        self.assertNotIn("candidate_track_id",report)
        self.assertEqual(device_hash("phone"),report["active_device_hash"])
        self.assertNotIn("phone",str(report))


if __name__ == "__main__": unittest.main()
