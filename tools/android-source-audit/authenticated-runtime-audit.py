#!/usr/bin/env python3
"""Bounded, account-owner-authorized lab UI. No credential output or customer privilege claim."""
import argparse,base64,hashlib,json,os,pathlib,re,subprocess,sys,tempfile,time,urllib.request,xml.etree.ElementTree as ET

OUT=pathlib.Path(os.environ['CELIKOM_LAB_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True)
ADB=os.environ['ANDROID_HOME']+'/platform-tools/adb'
REDACTIONS=[]
def age():return os.environ['RUNNER_TEMP']+'/age/age'
def cache_credentials(account):
 key=pathlib.Path(os.environ['RUNNER_TEMP'])/'celikom-lab-auth-identity'
 generated=subprocess.run([os.environ['RUNNER_TEMP']+'/age/age-keygen'],capture_output=True,check=True)
 with os.fdopen(os.open(key,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),'wb') as handle:handle.write(generated.stdout)
 public=subprocess.run([os.environ['RUNNER_TEMP']+'/age/age-keygen','-y',str(key)],capture_output=True,check=True).stdout.decode().strip()
 subprocess.run([age(),'-r',public,'-o',str(OUT/'session-auth.age')],input=json.dumps(account).encode(),capture_output=True,check=True)
def cached_credentials():
 p=subprocess.run([age(),'-d','-i',os.environ['RUNNER_TEMP']+'/celikom-lab-auth-identity',str(OUT/'session-auth.age')],capture_output=True,check=True)
 account=json.loads(p.stdout)
 REDACTIONS.extend(account.values())
 return account
def screenshot(name):
 p=subprocess.run([ADB,'-s','emulator-5554','exec-out','screencap','-p'],capture_output=True,timeout=60)
 if p.returncode:raise RuntimeError('screenshot_failed')
 subprocess.run([age(),'-r',os.environ['LAB_SCREEN_RECIPIENT'],'-o',str(OUT/(name+'.png.age'))],input=p.stdout,capture_output=True,check=True)
def adb(*args,timeout=90):
 p=subprocess.run([ADB,'-s','emulator-5554',*args],capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=timeout)
 if p.returncode:raise RuntimeError('adb_failed:'+args[0])
 return p.stdout
def request_json(url):
 req=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['INPUT_GITHUB_TOKEN'],'Accept':'application/vnd.github+json'})
 with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
def clean(value):
 s=str(value)
 for item in REDACTIONS:
  if item:s=s.replace(item,'[redacted]')
 return re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}','[email]',s)
def ui():
 adb('shell','-n','uiautomator','dump','/sdcard/lab-window.xml',timeout=60)
 root=ET.fromstring(adb('shell','-n','cat','/sdcard/lab-window.xml'))
 rows=[]
 for n in root.iter('node'):
  a=n.attrib
  row={k:clean(a.get(k,'')) for k in ('package','resource-id','class','text','content-desc','clickable','bounds','password')}
  if a.get('password')=='true':row['text']='[password field]'
  rows.append(row)
 return rows
def save(name,data):
 (OUT/name).write_text(clean(json.dumps(data,ensure_ascii=False,indent=2))+'\n')
def tap(n):
 v=list(map(int,re.findall(r'\d+',n['bounds'])))
 if len(v)!=4 or v[2]<=v[0] or v[3]<=v[1]:raise ValueError('offscreen_control')
 adb('shell','-n','input','tap',str((v[0]+v[2])//2),str((v[1]+v[3])//2))
def input_value(value):
 if not re.fullmatch(r'[A-Za-z0-9@._+%-]+',value):raise ValueError('unsupported_input_characters')
 adb('shell','-n','input','text',value)
def link(track):
 if not re.fullmatch(r'[1-9][0-9]{0,23}',track):raise ValueError('invalid_track_id')
 adb('shell','-n','am','start','-W','-a','android.intent.action.VIEW','-d','https://music.yandex.ru/track/'+track,'-p','ru.yandex.music')
def credentials():
 data=request_json('https://api.github.com/repos/manufact-test/nomusic/git/blobs/'+os.environ['AUTH_BLOB'])
 cipher=base64.b64decode(data['content'])
 assert hashlib.sha256(cipher).hexdigest()==os.environ['AUTH_CIPHER_HASH']
 fd,key=tempfile.mkstemp(prefix='lab-key-',dir=os.environ['RUNNER_TEMP'])
 try:
  with os.fdopen(fd,'w') as f:f.write(os.environ['INPUT_DECRYPT_KEY'].replace('\r','')+'\n')
  p=subprocess.run([os.environ['RUNNER_TEMP']+'/age/age','-d','-i',key],input=cipher,capture_output=True,timeout=30)
  if p.returncode:raise RuntimeError('credential_decryption_failed')
  account=json.loads(p.stdout)
 finally:os.unlink(key)
 for value in account.values():
  REDACTIONS.append(value)
  print('::add-mask::'+value,flush=True)
 return account
def authenticate():
 account=credentials()
 cache_credentials(account)
 paths=[str(pathlib.Path(os.environ['RUNNER_TEMP'])/'yandex-source'/n) for n in ('ru.yandex.music.apk','config.arm64_v8a.apk','config.en.apk','config.ru.apk','config.xhdpi.apk')]
 adb('install-multiple','-r',*paths,timeout=180)
 adb('shell','-n','am','start','-W','-n','ru.yandex.music/ru.yandex.music.main.MainScreenActivity')
 time.sleep(5);link('142820338');time.sleep(4)
 history=[];mail=False;password=False;status='unresolved'
 for step in range(18):
  nodes=ui();history.append({'step':step,'nodes':nodes})
  text=' '.join(n['text']+' '+n['content-desc'] for n in nodes).lower()
  password_choice=next((n for n in nodes if n['text'].strip().lower() in ('log in with a password','log in with password','use password','войти с паролем','войти по паролю')),None)
  if password_choice and mail and not password:tap(password_choice);time.sleep(3);continue
  if any(x in text for x in ("couldn't find your google account",'аккаунт не найден','такого аккаунта нет','account not found','неверный пароль','incorrect password','wrong password','неправильный пароль')):
   status='account_or_password_rejected';break
  if any(x in text for x in ('я не робот','not a robot','введите код','enter the code','код из смс','подтвердите, что вы')):
   status='owner_verification_required';break
  edits=[n for n in nodes if n['package'] in ('ru.yandex.music','com.google.android.gms') and n['class']=='android.widget.EditText']
  deny=next((n for n in nodes if n['resource-id'].endswith(':id/permission_deny_button')),None)
  if deny:tap(deny);time.sleep(2);continue
  if not edits and not any(n['text'] or n['content-desc'] for n in nodes) and any(n['class']=='android.webkit.WebView' for n in nodes):
   time.sleep(5);continue
  onboarding=next((n for n in nodes if n['class']=='android.widget.Button' and n['content-desc'].strip().lower()=='next' and not n['text'] and not edits),None)
  if onboarding:tap(onboarding);time.sleep(3);continue
  pwd=next((n for n in edits if n['password']=='true'),None)
  if pwd and not password:
   tap(pwd);input_value(account['password']);password=True
   nodes=ui()
   buttons=[n for n in nodes if n['class']=='android.widget.Button' and n['text'].strip().lower() in ('войти','продолжить','sign in','log in','continue','next','далее')]
   if buttons:tap(buttons[-1])
   else:adb('shell','-n','input','keyevent','66')
   time.sleep(6);continue
  authorize=next((n for n in nodes if n['resource-id'].endswith(':id/authorize')),None)
  if authorize:tap(authorize);time.sleep(4);continue
  # This owner supplied a Google test account. Use the offered provider button;
  # do not put its password into the separate Yandex-password form.
  google=next((n for n in nodes if n['package']=='ru.yandex.music' and n['class']=='android.widget.Button' and n['text'].strip()=='Google'),None)
  if google and not mail and any(s in text for s in ('enter your phone number','введите номер телефона')):
   tap(google);time.sleep(10);continue
  mail_choice=next((n for n in nodes if n['text'].strip().lower() in ('почта','почта или логин','логин','email','email or username','username','войти по логину')),None)
  if not mail and mail_choice:
   tap(mail_choice);time.sleep(2);nodes=ui();edits=[n for n in nodes if n['class']=='android.widget.EditText']
  if edits and not mail and not pwd and not any(s in text for s in ('enter your phone number','введите номер телефона')):
   tap(edits[0]);input_value(account['login']);mail=True
   nodes=ui()
   buttons=[n for n in nodes if n['class']=='android.widget.Button' and n['text'].strip().lower() in ('войти','продолжить','sign in','log in','continue','next','далее')]
   if buttons:tap(buttons[-1])
   else:adb('shell','-n','input','keyevent','66')
   time.sleep(5);continue
  if password and not edits:
   status='password_submitted_no_auth_fields';break
  safe=next((n for n in nodes if n['class']=='android.widget.Button' and n['text'].strip().lower() in ('другие способы входа','other login methods','other ways to sign in','продолжить','continue','понятно','ok','log in','sign in','войти','log in with yandex','войти через яндекс')),None)
  if safe:tap(safe);time.sleep(3);continue
  status='unrecognized_auth_screen';break
 save('auth-report.json',{'status':status,'mail_entered':mail,'password_entered':password,'history':history,'nodes':ui(),'automatic_catalogue_id_verified':False})
 screenshot('auth-checkpoint')
 print(json.dumps({'auth_status':status,'password_submitted':password,'automatic_catalogue_id_verified':False}))
def observer_report():
 try:
  xml=adb('shell','-n','run-as','pro.celikom.nativeprobe','cat','shared_prefs/native_probe.xml')
  root=ET.fromstring(xml)
  allowed={'public_media','public_media_history','track_identity','session_identity','public_browser','service_discovery','media3_error','legacy_identity'}
  return {n.attrib['name']:json.loads(n.text) for n in root if n.attrib.get('name') in allowed}
 except Exception as e:return {'status':type(e).__name__}
def execute(op):
 kind=op['op']
 if kind=='stop':(OUT/'stop').touch();return {'operation':'stop'}
 elif kind=='tap':adb('shell','-n','input','tap',str(int(op['x'])),str(int(op['y'])))
 elif kind=='key':adb('shell','-n','input','keyevent',str(int(op['code'])))
 elif kind=='link':link(op['id'])
 elif kind=='launch_yandex':adb('shell','-n','am','start','-W','-n','ru.yandex.music/ru.yandex.music.main.MainScreenActivity')
 elif kind=='observer':
  adb('install','-r',os.environ['RUNNER_TEMP']+'/observer.apk',timeout=90)
  adb('shell','-n','am','start','-W','-n','pro.celikom.nativeprobe/.MainActivity')
 elif kind in ('fill_login','fill_password'):
  account=cached_credentials();nodes=ui();pwd=kind=='fill_password'
  fields=[n for n in nodes if n['package'] in ('ru.yandex.music','com.google.android.gms') and n['class']=='android.widget.EditText' and (n['password']=='true')==pwd]
  if not fields:raise RuntimeError('expected_login_provider_input_missing')
  if not pwd and any('enter your phone number' in n['text'].lower() for n in nodes):raise RuntimeError('phone_method_still_selected')
  tap(fields[0]);input_value(account['password' if pwd else 'login'])
  if op.get('submit'):
   nodes=ui();buttons=[n for n in nodes if n['class']=='android.widget.Button' and n['text'].strip().lower() in ('войти','продолжить','sign in','log in','continue','next','далее')]
   if buttons:tap(buttons[-1])
   else:adb('shell','-n','input','keyevent','66')
 elif kind=='swipe':adb('shell','-n','input','swipe',str(int(op['x1'])),str(int(op['y1'])),str(int(op['x2'])),str(int(op['y2'])),'300')
 elif kind=='trace':
  adb('root');adb('wait-for-device');adb('push',os.environ['RUNNER_TEMP']+'/frida-server','/data/local/tmp/celikom-lab-frida')
  adb('shell','-n','chmod','700','/data/local/tmp/celikom-lab-frida')
  subprocess.Popen([ADB,'-s','emulator-5554','shell','-n','/data/local/tmp/celikom-lab-frida'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  time.sleep(2);adb('forward','tcp:27042','tcp:27042')
  env=dict(os.environ,PYTHONPATH=os.environ['RUNNER_TEMP']+'/frida-python')
  subprocess.Popen([sys.executable,str(pathlib.Path(__file__).with_name('trace.py'))],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 elif kind!='capture':raise ValueError('unknown_lab_operation')
 time.sleep(min(int(op.get('wait',3)),10))
 return {'operation':kind,'nodes':ui(),'ordinary_observer':observer_report()}
def command(seq):
 if (OUT/'stop').exists():save('round-'+str(seq)+'.json',{'status':'stopped'});return
 deadline=time.monotonic()+180
 while time.monotonic()<deadline:
  try:
   data=request_json('https://api.github.com/repos/manufact-test/nomusic/contents/.github/lab/yandex-runtime-command.json?ref=feature/api-range')
   c=json.loads(base64.b64decode(data['content']))
   if str(c.get('run_id'))==os.environ['GITHUB_RUN_ID'] and c.get('seq')==seq:
    ops=c['ops']
    if len(ops)>8:raise ValueError('operation_limit')
    results=[]
    for index,op in enumerate(ops):
     try:
      results.append(execute(op))
      if op['op']!='stop':screenshot('round-'+str(seq)+'-op-'+str(index))
     except Exception as error:
      results.append({'operation':op.get('op'),'error_type':type(error).__name__,'detail':clean(str(error))[:200]})
      break
    save('round-'+str(seq)+'.json',{'seq':seq,'results':results,'automatic_catalogue_id_verified':False});return
  except urllib.error.HTTPError as e:
   if e.code!=404:raise
  time.sleep(8)
 save('round-'+str(seq)+'.json',{'seq':seq,'status':'instruction_timeout'})
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['auth','command']);parser.add_argument('--seq',type=int,default=0);a=parser.parse_args()
 try:
  if a.mode=='auth':authenticate()
  else:command(a.seq)
 except Exception as e:
  save('failure-'+a.mode+'.json',{'error_type':type(e).__name__,'detail':clean(str(e))[:200]})
  if a.mode=='auth':
   try:
    save('auth-failure-ui.json',{'nodes':ui(),'automatic_catalogue_id_verified':False})
    screenshot('auth-checkpoint')
   except Exception:pass
  print('Laboratory step failed:',type(e).__name__);sys.exit(1)
