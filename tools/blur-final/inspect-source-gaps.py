#!/usr/bin/env python3
"""Inspect pinned FckCensorData source audio tags for 28 unmapped IDs.
No production access, no database changes and no upload manifest mutation.
"""
import csv, hashlib, json, pathlib, subprocess, tempfile, urllib.request, time
SOURCE="Hazzz895/FckCensorData"
COMMIT="10187b7af56f311fe141a3c9b75483798bf0f589"
rows=list(csv.DictReader(open("docs/research/BLUR-SOURCE-GAPS.csv",encoding="utf-8")))
eligible=[r for r in rows if r["reason"]=="unmapped_artist_title"]
assert len(eligible)==28 and len({r["track_id"] for r in eligible})==28
with urllib.request.urlopen(urllib.request.Request(f"https://api.github.com/repos/{SOURCE}/git/trees/{COMMIT}?recursive=1",headers={"User-Agent":"CELIKOM-readonly-source-metadata-audit"}),timeout=45) as handle:
    tree=json.load(handle)
by_path={o["path"]:o for o in tree["tree"] if o["type"]=="blob"}
results=[]
with tempfile.TemporaryDirectory() as folder:
    for i,item in enumerate(eligible,1):
        tid=item["track_id"]
        src=by_path.get("tracks/"+tid)
        result={"track_id":tid,"size":int(item["source_bytes"]),"git_blob":src["sha"] if src else None,"status":"pending"}
        if not src or int(src["size"])!=int(item["source_bytes"]):
            result["status"]="source_metadata_mismatch"
            results.append(result)
            continue
        path=pathlib.Path(folder)/(tid+".mp3")
        for retry in range(3):
            try:
                u=f"https://raw.githubusercontent.com/{SOURCE}/{COMMIT}/tracks/{tid}"
                req=urllib.request.Request(u,headers={"User-Agent":"CELIKOM-readonly-source-tags"})
                with urllib.request.urlopen(req,timeout=60) as stream, path.open("wb") as out:
                    h=hashlib.sha1(b"blob "+str(src["size"]).encode()+b"\\0")
                    total=0
                    while block:=stream.read(262144):
                        out.write(block);h.update(block);total+=len(block)
                if total!=src["size"] or h.hexdigest()!=src["sha"]:
                    result["status"]="hash_mismatch"
                else:
                    mime=subprocess.run(["file","-b","--mime-type",str(path)],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
                    probe=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:format_tags=title,artist,album","-of","json",str(path)],capture_output=True,text=True,timeout=60)
                    info=json.loads(probe.stdout) if probe.returncode==0 and probe.stdout.strip() else {}
                    result.update({"status":"checked","mime":mime,"duration":info.get("format",{}).get("duration"),"tags":info.get("format",{}).get("tags",{})})
                break
            except (OSError,subprocess.SubprocessError,ValueError) as e:
                result["status"]="transient_error"
                result["error"]=type(e).__name__
                if retry<2:time.sleep(2+retry)
            finally:
                path.unlink(missing_ok=True)
        results.append(result)
        print("SOURCE_GAP_TAGS "+json.dumps(result,ensure_ascii=False,separators=(",",":")),flush=True)
summary={"checked":len(results),"normal_mp3":sum(x.get("mime")=="audio/mpeg" for x in results),"with_title_artist_tags":sum(bool(x.get("tags",{}).get("title") and x.get("tags",{}).get("artist")) for x in results),"no_tags":sum(not x.get("tags") for x in results),"transient":sum(x.get("status")=="transient_error" for x in results),"production_writes":0}
pathlib.Path("source-gaps-audit.json").write_text(json.dumps({"summary":summary,"results":results},indent=2,ensure_ascii=False)+"\\n",encoding="utf-8")
print("SOURCE_GAPS_AUDIT_SUMMARY "+json.dumps(summary,ensure_ascii=False),flush=True)
