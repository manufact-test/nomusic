from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parent;addon=r.parent/'addon/src/pro/celikom/nativeprobe/identitydiag';out=r/'classes';out.mkdir(exist_ok=True);json=r.parent/'deps/json.jar'
subprocess.run(['python3',r/'write_fakes.py'],check=True)
src=[*sorted((r/'fakes').rglob('*.java')),r/'TestEngine.java',r/'TestPhoneReplay.java',*[addon/n for n in ['ApiContract.java','AlbumMatch.java','PlaybackSource.java','ReplacementEngine.java']]]
subprocess.run(['java','com.sun.tools.javac.Main','-encoding','UTF-8','-source','8','-target','8','-cp',str(json),'-d',str(out),*map(str,src)],check=True)
subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestEngine'],check=True)

subprocess.run(['java','-cp',str(out)+os.pathsep+str(json),'pro.celikom.nativeprobe.identitydiag.TestPhoneReplay',str(r/'phone-0.3.20-replay.tsv')],check=True)
