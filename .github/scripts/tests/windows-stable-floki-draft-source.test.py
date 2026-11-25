import copy
import pathlib
import runpy
import unittest
import urllib.request

core = runpy.run_path(str(pathlib.Path(__file__).resolve().parents[1] / "windows-stable-floki-draft-source.py"))
plan = core["asset_plan"]
version = "0.24.55"
commit = "61d17d9eb97f3db5c58c906e30da6c19ee737090"


def fixture():
    def asset(name, size, n, digest="a"*64):
        return dict(id=n,name=name,size=size,digest="sha256:"+digest)
    return [
        dict(draft=True,tag_name="celikom-windows-v"+version+"-owner-bootstrap",target_commitish=commit,
             assets=[asset("CELIKOM-Windows-"+version+".exe",85145078,1),
                     asset("CELIKOM-Windows-"+version+".zip",84665224,2),asset("SHA256SUMS.txt",198,3)]),
        dict(draft=True,tag_name="celikom-windows-v"+version+"-floki-feed-candidate",target_commitish=commit,
             assets=[asset("latest.json",851,4),asset("latest.json.sig",71,5),
                     asset("manifest-public-key.der",91,6,core["PIN_SHA256"]),
                     asset("manifest.json",851,7),asset("manifest.json.sig",71,8)])
    ]


class DraftSourceTests(unittest.TestCase):
    def test_exact_six_files_only(self):
        self.assertEqual(set(plan(fixture(),version,2,commit)),
                         {"latest.json","latest.json.sig","manifest-public-key.der",
                          version+"/manifest.json",version+"/manifest.json.sig",
                          version+"/CELIKOM-Windows-"+version+".exe"})

    def test_public_wrong_source_duplicate_and_missing_draft_refused(self):
        for change in ("public","source","duplicate","missing"):
            rows=fixture()
            if change=="public": rows[0]["draft"]=False
            elif change=="source": rows[1]["target_commitish"]="f"*40
            elif change=="duplicate": rows.append(copy.deepcopy(rows[0]))
            else: rows.pop()
            with self.assertRaises(ValueError): plan(rows,version,2,commit)

    def test_unexpected_asset_size_digest_or_pin_refused(self):
        for field,value in (("name","../file"),("size",126000000),("digest","sha256:"+"b"*64),("id",None)):
            rows=fixture()
            rows[1]["assets"][2][field]=value
            with self.assertRaises(ValueError): plan(rows,version,2,commit)

    def test_unsafe_identity_refused(self):
        for v,s,c in (("../bad",2,commit),(version,0,commit),(version,2,"main"),(version,2**53,commit)):
            with self.assertRaises(ValueError): plan(fixture(),v,s,c)


    def test_authenticated_api_redirect_never_leaks_bearer_to_asset_cdn(self):
        request = urllib.request.Request(
            "https://api.github.com/repos/manufact-test/nomusic/releases/assets/42",
            headers={"Authorization": "Bearer do-not-send-to-cdn",
                     "Accept": "application/octet-stream"})
        handler = core["SafeAssetRedirect"]()
        next_request = handler.redirect_request(request, None, 302, "",
            {}, "https://release-assets.githubusercontent.com/example")
        self.assertIsNone(next_request.get_header("Authorization"))
        self.assertIsNone(next_request.get_header("Accept"))
        for bad in ("http://release-assets.githubusercontent.com/unsafe",
                    "https://evil.example/asset", "https://github.com/other"):
            with self.assertRaises(ValueError):
                handler.redirect_request(request, None, 302, "", {}, bad)

    def test_api_endpoint_is_pinned_to_repository_and_token_is_required(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"GH_TOKEN": "X"*40}):
            req = core["github_request"]("/repos/manufact-test/nomusic/releases/assets/42")
            self.assertEqual(req.get_header("Authorization"), "Bearer " + "X"*40)
            for bad in ("/repos/other/private/releases", "/other", "https://evil.example"):
                with self.assertRaises(ValueError):
                    core["github_request"](bad)



if __name__=="__main__": unittest.main()
