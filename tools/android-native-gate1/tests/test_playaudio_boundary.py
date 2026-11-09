"""PlayAudio boundary scanner safety/structural tests; NO real APK included."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_inspect_android_host import synthetic_dex
from inspect_android_host import Dex,DexError
from trace_playaudio_boundary import trace_playaudio,_encoded_value

def fixture(extra):
    d=bytearray(synthetic_dex())
    d.extend(extra)
    import struct
    struct.pack_into("<I",d,32,len(d))
    return Dex(bytes(d)),len(d)-len(extra)

class PlayAudioTests(unittest.TestCase):
    def test_unrelated_dex_is_not_a_hook(self):
        r=trace_playaudio(synthetic_dex())
        self.assertEqual(r["invocation_count"],0)
        self.assertEqual(r["retrofit_static_routes"],[])
        self.assertEqual(r["verdict"],"STATIC_CANDIDATES_ONLY_NO_PROVEN_ACTIVE_PLAYER_HOOK")

    def test_string_value_is_decoded_but_not_published_automatically(self):
        dex,pos=fixture(b"\x17\x03")
        v,p=_encoded_value(dex,pos)
        self.assertEqual(v,"createMediaSource")
        self.assertEqual(p,pos+2)

    def test_encoded_bool(self):
        dex,pos=fixture(b"\x3f")
        self.assertEqual(_encoded_value(dex,pos),(True,pos+1))

    def test_null(self):
        dex,pos=fixture(b"\x1e")
        self.assertEqual(_encoded_value(dex,pos),(None,pos+1))

    def test_rejects_malformed_value(self):
        dex,pos=fixture(b"\x01")
        with self.assertRaises(DexError):
            _encoded_value(dex,pos)

    def test_array_does_not_leak_data(self):
        dex,pos=fixture(b"\x1c\x01\x17\x03")
        self.assertEqual(_encoded_value(dex,pos),(None,pos+4))

if __name__=="__main__":
    unittest.main()
