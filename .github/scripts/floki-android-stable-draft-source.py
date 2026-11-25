#!/usr/bin/env python3
"""Read exact signed legacy Android private draft assets into isolated CI.

GitHub is an internal build source, never a customer or owner download endpoint.
No server SSH, production filesystem mount, signing key, or publisher credentials.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request

REPO="manufact-test/nomusic"
API="https://api.github.com"
CERT="67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"
PKG="pro.celikom.nativeprobe"
HEX=re.compile(r"[0-9a-f]{64}\Z")
VERSION=re.compile(r"0\.3\.[0-9]{1,4}\Z")


def need(value,code):
    if not value:
        raise RuntimeError("ANDROID_STABLE_DRAFT_"+code)


class GitHubAssetRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        x=urllib.parse.urlsplit(newurl)
        need(x.scheme=="https" and x.hostname in
             {"release-assets.githubusercontent.com","objects.githubusercontent.com"},
             "UNTRUSTED_REDIRECT")
        nxt=super().redirect_request(req,fp,code,msg,headers,newurl)
        if nxt:
            nxt.remove_header("Authorization")
            nxt.remove_header("Accept")
        return nxt


def request(path,accept="application/vnd.github+json"):
    token=os.getenv("GH_TOKEN","")
    need(len(token)>=20,"GITHUB_TOKEN_REQUIRED")
    need(path=="/repos/"+REPO or path.startswith("/repos/"+REPO+"/"),"ENDPOINT_NOT_APPROVED")
    return urllib.request.Request(API+path,headers={
        "Authorization":"Bearer "+token,
        "Accept":accept,
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"CELIKOM-Android-Stable-Data-Only"
    })


def read_json(path):
    with urllib.request.urlopen(request(path),timeout=40) as r:
        need(r.url==API+path,"API_REDIRECT_REFUSED")
        raw=r.read(2_000_001)
        need(len(raw)<=2_000_000,"API_OVERSIZE")
        return json.loads(raw)


def download(asset,out):
    link="/repos/"+REPO+"/releases/assets/"+str(asset["id"])
    client=urllib.request.build_opener(GitHubAssetRedirect())
    req=request(link,"application/octet-stream")
    digest=hashlib.sha256()
    size=0
    with client.open(req,timeout=180) as r,out.open("xb") as f:
        address=urllib.parse.urlsplit(r.geturl())
        need(address.scheme=="https" and address.hostname in
             {"release-assets.githubusercontent.com","objects.githubusercontent.com"},
             "ASSET_ORIGIN_INVALID")
        while chunk:=r.read(1024*1024):
            size+=len(chunk)
            need(size<=asset["size"],"ASSET_TOO_LARGE")
            digest.update(chunk)
            f.write(chunk)
        f.flush()
        os.fsync(f.fileno())
    need(size==asset["size"] and
         "sha256:"+digest.hexdigest()==asset["digest"],"ASSET_DIGEST_INVALID")


def prepare(req_path,output):
    q=json.loads(req_path.read_text())
    need(isinstance(q,dict) and set(q)=={
        "release_id","source_run","attempt","version","version_code",
        "apk_sha256","apk_size","manifest_sha256"
    },"REQUEST_FIELDS")
    need(type(q["release_id"]) is int and q["release_id"]>0
         and type(q["source_run"]) is int and q["source_run"]>0
         and type(q["attempt"]) is int and 1<=q["attempt"]<=100
         and type(q["version_code"]) is int and q["version_code"]>=95
         and isinstance(q["version"],str) and VERSION.fullmatch(q["version"])
         and isinstance(q["apk_sha256"],str) and HEX.fullmatch(q["apk_sha256"])
         and isinstance(q["manifest_sha256"],str) and HEX.fullmatch(q["manifest_sha256"])
         and type(q["apk_size"]) is int and 100_000<=q["apk_size"]<=200*1024*1024,
         "REQUEST_INVALID")
    repo=read_json("/repos/"+REPO)
    need(repo.get("private") is True,"PRIVATE_REPO_REQUIRED")
    release=read_json("/repos/"+REPO+"/releases/"+str(q["release_id"]))
    need(release.get("draft") is True and
         release.get("tag_name")==
          f'celikom-legacy-bridge-private-{q["source_run"]}-{q["attempt"]}',
         "PRIVATE_DRAFT_IDENTITY")
    items={x.get("name"):x for x in release["assets"]}
    apk_name=f'CELIKOM-Android-{q["version"]}-SIGNED.apk'
    expected={apk_name:(q["apk_size"],q["apk_sha256"]),
              "stable-floki-candidate.json":(None,q["manifest_sha256"])}
    need(set(expected).issubset(items),"MISSING_DRAFT_ASSETS")
    output.mkdir(mode=0o700,parents=True,exist_ok=False)
    for name,(size,digest) in expected.items():
        a=items[name]
        need(type(a.get("id")) is int and a["id"]>0
             and type(a.get("size")) is int and 100<=a["size"]<=200*1024*1024
             and (size is None or size==a["size"])
             and a["digest"]=="sha256:"+digest,
             "ASSET_METADATA_MISMATCH")
        download(a,output/name)
    proof={
        "source_run":q["source_run"],"source_attempt":q["attempt"],
        "version":q["version"],"version_code":q["version_code"],
        "apk_sha256":q["apk_sha256"],"apk_size":q["apk_size"],
        "apk_name":apk_name,"signer_sha256":CERT,"package":PKG
    }
    (output/"proof.json").write_text(json.dumps(proof,sort_keys=True)+"\n")
    os.chmod(output/"proof.json",0o600)
    print("ANDROID_STABLE_SIGNED_PRIVATE_DRAFT_BYTES_VERIFIED",
          q["version"],q["version_code"],q["apk_sha256"])


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--request",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    args=a.parse_args()
    prepare(args.request,args.output)
