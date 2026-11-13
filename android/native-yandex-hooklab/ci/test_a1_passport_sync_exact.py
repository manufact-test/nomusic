"""Pure synthetic checks for single-string Android table rewrite (no vendor bytes)."""
import struct
import unittest
from a1_passport_sync_exact import (
    PassportResourceMismatch, rewrite_exact_sync_authority,
    rewrite_exact_owned_account_type, _strings)

OLD = 'ru.yandex.music'
OWN = 'pro.celikom.yandex.nativeclonelab'
PREFIX = 'com.yandex.passport.sync.'

def table(strings):
    payload=bytearray()
    offsets=[]
    for s in strings:
        raw=s.encode('utf8')
        assert len(raw)<128
        offsets.append(len(payload))
        payload+=bytes([len(s),len(raw)])+raw+b'\0'
    while len(payload)%4:
        payload+=b'\0'
    header=28
    start=header+4*len(strings)
    size=start+len(payload)
    pool=struct.pack('<HHI5I',1,header,size,len(strings),0,256,start,0)
    pool+=b''.join(struct.pack('<I',x) for x in offsets)+payload
    tail=b'\x00\x02\x08\x00\x08\x00\x00\x00'
    return struct.pack('<HHII',2,12,12+len(pool)+len(tail),1)+pool+tail

class Tests(unittest.TestCase):
    def test_target_only(self):
        before=table(['unrelated',PREFIX+OLD,'other'])
        after=rewrite_exact_sync_authority(before,OLD,OWN)
        s,_,_=_strings(after)
        self.assertEqual([x[0] for x in s],['unrelated',PREFIX+OWN,'other'])
        self.assertEqual(after[-8:],before[-8:])
    def test_owned_authenticator_and_sync_use_distinct_strings(self):
        before=table(['com.yandex.passport',PREFIX+OLD,'unrelated'])
        sync=rewrite_exact_sync_authority(before,OLD,OWN)
        after=rewrite_exact_owned_account_type(sync,OLD,OWN)
        actual=[x[0] for x in _strings(after)[0]]
        self.assertEqual(actual,[OWN+'.passport',PREFIX+OWN,'unrelated'])
        self.assertEqual(after[-8:],before[-8:])
        with self.assertRaises(PassportResourceMismatch):
            rewrite_exact_owned_account_type(after,OLD,OWN)

    def test_reject_duplicate_owned_type(self):
        before=table(['com.yandex.passport','com.yandex.passport'])
        with self.assertRaises(PassportResourceMismatch):
            rewrite_exact_owned_account_type(before,OLD,OWN)

    def test_reject_foreign_names(self):
        with self.assertRaises(PassportResourceMismatch):
            rewrite_exact_owned_account_type(table(['com.yandex.passport']),
                'someone.else','com.yandex.passport')

    def test_reject_missing(self):
        with self.assertRaises(PassportResourceMismatch):
            rewrite_exact_sync_authority(table(['unrelated']),OLD,OWN)
    def test_reject_duplicate(self):
        with self.assertRaises(PassportResourceMismatch):
            rewrite_exact_sync_authority(table([PREFIX+OLD,PREFIX+OLD]),OLD,OWN)
    def test_reject_repeat(self):
        patched=rewrite_exact_sync_authority(table([PREFIX+OLD]),OLD,OWN)
        with self.assertRaises(PassportResourceMismatch):
            rewrite_exact_sync_authority(patched,OLD,OWN)

if __name__=='__main__':
    unittest.main()
