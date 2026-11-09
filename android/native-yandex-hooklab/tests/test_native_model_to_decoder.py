import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trace_native_model_to_decoder import is_model_method,is_media_call,bounded_obfuscated

class DownstreamClassifyTests(unittest.TestCase):
    def test_exact_model_signature(self):
        self.assertTrue(is_model_method(("Lfgh;","a","(Leed;Z)Ljava/lang/Object;")))
        self.assertTrue(is_model_method(("Leed;","a","()V")))
        self.assertFalse(is_model_method(("Lxyz;","a","(Ljava/lang/String;)V")))
    def test_media_source_api_not_telemetry(self):
        self.assertTrue(is_media_call(("Landroidx/media3/exoplayer/source/DefaultMediaSourceFactory;","createMediaSource","()V")))
        self.assertTrue(is_media_call(("Landroidx/media3/exoplayer/ExoPlayerImpl;","prepare","()V")))
        self.assertFalse(is_media_call(("Lcom/yandex/analytics/PlayAudioApi;","prepare","()V")))
        self.assertFalse(is_media_call(("Landroidx/media3/common/MediaItem;","toString","()Ljava/lang/String;")))
    def test_no_private_output(self):
        self.assertEqual(bounded_obfuscated(("Lcom/yandex/music/PrivateTokenManager;","getKey","()Ljava/lang/String;")),"named-other-class")
        self.assertEqual(bounded_obfuscated(("Lsw7;","y0","(I)V")),"exact-fileinfo-converter")
if __name__=="__main__":unittest.main()
