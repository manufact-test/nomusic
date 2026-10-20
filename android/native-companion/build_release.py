from pathlib import Path
import subprocess,zipfile,xml.etree.ElementTree as ET,json,hashlib,os,shutil,io
r=Path(__file__).resolve().parent;ws=r.parent;original=r/'decoded';addon=r/'addon';b=addon/'build';sdk=ws/'android-build/sdk';bt=sdk/'build-tools/android-16';android=sdk/'platforms/android-36/android.jar';private=r/'private';out=ws/'outputs/CELIKOM-0.3.22-install.apk'
def run(args):subprocess.run(list(map(str,args)),check=True)
assert hashlib.sha256((ws/'recovered/CELIKOM-0.3.17-install.apk').read_bytes()).hexdigest()=='a3c951441fc1847381074b84508b4b2fdd58d29e7e3a4d02f9ddbb627aa94dc2'
ns='http://schemas.android.com/apk/res/android';ET.register_namespace('android',ns);a=lambda n:'{'+ns+'}'+n
manifest=original/'AndroidManifest.xml';tree=ET.parse(manifest);root=tree.getroot();app=root.find('application');app.set(a('usesCleartextTraffic'),'false')
for node in list(app):
 if node.tag=='service' and node.get(a('name'))=='pro.celikom.nativeprobe.identitydiag.RecorderListener':app.remove(node)
 if node.tag=='service' and node.get(a('name'))=='pro.celikom.nativeprobe.identitydiag.ProbeService':
  node.set(a('foregroundServiceType'),'specialUse|mediaPlayback')
  node.find('property').set(a('value'),'Owner initiated bounded current-song observation, server availability check and owner enabled automatic audio replacement within a bounded foreground run')
assert not any(n.get(a('permission'))=='android.permission.BIND_NOTIFICATION_LISTENER_SERVICE' for n in app)
assert not any(n.get(a('permission'))=='android.permission.BIND_ACCESSIBILITY_SERVICE' for n in app)
tree.write(manifest,encoding='utf-8',xml_declaration=True)
yml=original/'apktool.yml';s=yml.read_text().replace('versionCode: 22','versionCode: 23').replace('0.3.21-probe','0.3.22-probe');yml.write_text(s)
for p in (original/'smali/pro/celikom/nativeprobe').rglob('*.smali'):
 s=p.read_text().replace('0.3.21-probe','0.3.22-probe')
 if p.name=='BuildConfig.smali':
  import re
  s=re.sub(r'(\.field public static final VERSION_CODE:I = )0x[0-9a-f]+',r'\g<1>0x17',s)
 p.write_text(s)
shutil.rmtree(original/'smali_classes2',ignore_errors=True)
jars=[p for p in sorted((r/'deps').glob('*.jar')) if p.name!='json.jar'];cp=os.pathsep.join(map(str,[android,*jars]));shutil.rmtree(b/'classes',ignore_errors=True);(b/'classes').mkdir(parents=True)
run(['java','com.sun.tools.javac.Main','-encoding','UTF-8','-source','8','-target','8','-cp',cp,'-d',b/'classes',*sorted((addon/'src').rglob('*.java'))])
(b/'tests').mkdir(exist_ok=True)
run(['java','com.sun.tools.javac.Main','-encoding','UTF-8','-source','8','-target','8','-cp',str(r/'deps/json.jar')+os.pathsep+str(b/'classes')+os.pathsep+str(android),'-d',b/'tests',*sorted(addon.glob('Test*.java'))])
run(['python3',r/'tests/run_engine.py'])
for test in ['TestPure','TestHybrid','TestContracts']:run(['java','-cp',os.pathsep.join(map(str,[r/'deps/json.jar',b/'classes',b/'tests',android])), 'pro.celikom.nativeprobe.identitydiag.'+test])
run(['java','sun.tools.jar.Main','--create','--file',b/'addon.jar','-C',b/'classes','.']);(b/'dex').mkdir(exist_ok=True)
args=['java','-Xmx1500m','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',android,'--output',b/'dex']
for jar in jars:args+=['--classpath',jar]
run([*args,b/'addon.jar'])
source=io.BytesIO()
with zipfile.ZipFile(source,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in [*sorted((addon/'src').rglob('*.java')),*sorted(addon.glob('Test*.java')),r/'build_release.py',addon/'README.md',manifest,yml,*[p for p in sorted((r/'tests').rglob('*')) if p.is_file() and p.suffix in ('.py','.java','.tsv')]]:z.write(p,'CELIKOM-0.3.22-source/'+str(p.relative_to(r)))
(original/'assets/identity-integration-source.zip').write_bytes(source.getvalue())
run(['java','-jar',ws/'tools/apktool.jar','b',original,'-o',r/'unsigned.apk'])
with zipfile.ZipFile(r/'unsigned.apk','a',compression=zipfile.ZIP_DEFLATED) as z:
 for p in sorted((b/'dex').glob('*.dex')):
  name='classes2.dex' if p.name=='classes.dex' else 'classes'+str(int(p.stem[7:])+1)+'.dex';assert name not in z.namelist();z.write(p,name)
run([bt/'zipalign','-f','4',r/'unsigned.apk',r/'aligned.apk'])
metadata=json.loads((private/'signing.json').read_text())
for name,key in [('store-password','store_password'),('key-password','key_password')]:p=private/name;p.write_text(metadata[key]);p.chmod(0o600)
run(['java','-jar',bt/'lib/apksigner.jar','sign','--ks',private/'celikom-native-probe.p12','--ks-key-alias',metadata['alias'],'--ks-pass','file:'+str(private/'store-password'),'--key-pass','file:'+str(private/'key-password'),'--out',out,r/'aligned.apk'])
run(['java','-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',out]);run([bt/'zipalign','-c','4',out]);print('APK',out,'BYTES',out.stat().st_size,'SHA256',hashlib.sha256(out.read_bytes()).hexdigest())
