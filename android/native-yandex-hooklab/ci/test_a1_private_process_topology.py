import unittest
from a1_private_process_topology import parse_manifest,summarize

class ProcessTopologyTest(unittest.TestCase):
    def test_nested_intent_filter_must_not_overwrite_service_name(self):
        tree='''E: manifest
  E: application
    E: service
      A: android:name(0x01010003)="com.test.AudioPlaybackService"
      A: android:process(0x01010011)=":player"
      E: intent-filter
        E: action
          A: android:name(0x01010003)="android.intent.action.OTHER"
    E: service
      A: android:name(0x01010003)="com.test.AccountSyncService"
      A: android:process(0x01010011)=":passport"
'''
        rows=parse_manifest(tree)
        self.assertEqual(len([x for x in rows if x['tag']=='service']),2)
        result=summarize(rows)
        self.assertEqual(result['services'],2)
        self.assertEqual(result['media_named_services'],1)
        self.assertEqual(result['media_named_separate_process'],1)
        self.assertEqual(result['service_separate_process'],2)

    def test_main_service_is_not_secondary(self):
        tree='''E: manifest
  E: application
    E: service
      A: android:name(0x01010003)="com.test.MediaService"
'''
        result=summarize(parse_manifest(tree))
        self.assertEqual(result['media_named_main_process'],1)
        self.assertEqual(result['media_named_separate_process'],0)

if __name__=='__main__':unittest.main()
