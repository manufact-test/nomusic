import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_obfuscated_datasource_shape import api_shape_census


class ObfuscatedDataSourceShapeTests(unittest.TestCase):
    def test_full_data_source_interface_like_methods_are_only_signatures(self):
        m={
            ("Lm48;","b","(La58;)J"),
            ("Lv38;","read","([BII)I"),
            ("Lm48;","close","()V"),
            ("Lm48;","getUri","()Landroid/net/Uri;"),
        }
        out=api_shape_census(m)
        self.assertTrue(out["data_source_like_signature_complete"])
        self.assertFalse(out["actual_instantiated_music_decoder_datasource_proven"])

    def test_no_false_positive_for_only_geturi_and_close(self):
        m={
            ("Lm48;","close","()V"),
            ("Lm48;","getUri","()Landroid/net/Uri;"),
        }
        out=api_shape_census(m)
        self.assertFalse(out["data_source_like_signature_complete"])
        self.assertFalse(out["byte_array_read_signature"])

    def test_data_spec_argument_must_be_exact_type(self):
        m={
            ("Lm48;","b","(Lother;)J"),
            ("Lm48;","read","([BII)I"),
            ("Lm48;","close","()V"),
            ("Lm48;","getUri","()Landroid/net/Uri;"),
        }
        out=api_shape_census(m)
        self.assertFalse(out["dataspec_to_long_signature"])
        self.assertFalse(out["data_source_like_signature_complete"])

    def test_inherited_data_reader_and_source_method_union(self):
        source={
            ("Lm48;","b","(La58;)J"),
            ("Lm48;","close","()V"),
            ("Lm48;","getUri","()Landroid/net/Uri;"),
        }
        parent={("Lv38;","read","([BII)I")}
        self.assertFalse(api_shape_census(source)["data_source_like_signature_complete"])
        self.assertFalse(api_shape_census(parent)["data_source_like_signature_complete"])
        combined=api_shape_census(source|parent)
        self.assertTrue(combined["data_source_like_signature_complete"])
        self.assertFalse(combined["actual_instantiated_music_decoder_datasource_proven"])

    def test_wrong_return_type_does_not_count(self):
        m={
            ("Lm48;","b","(La58;)I"),
            ("Lm48;","read","([BII)I"),
            ("Lm48;","close","()V"),
            ("Lm48;","getUri","()Landroid/net/Uri;"),
        }
        out=api_shape_census(m)
        self.assertFalse(out["data_source_like_signature_complete"])


if __name__=="__main__":
    unittest.main()
