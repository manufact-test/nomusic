import frida,json,pathlib,time,os
root=pathlib.Path(__file__).resolve().parent
out=(pathlib.Path(os.environ.get('CELIKOM_LAB_OUTPUT',str(root)))/'trace.jsonl').open('a',buffering=1)
def write(data):out.write(json.dumps(data,ensure_ascii=False)+'\n')
try:
 device=frida.get_device_manager().add_remote_device('127.0.0.1:27042')
 pid=next(p.pid for p in device.enumerate_processes() if p.name=='ru.yandex.music')
 session=device.attach(pid)
 script=session.create_script((root/'trace.js').read_text())
 def receive(message,data):
  if message['type']=='send':write(message['payload'])
  elif message['type']=='error':write({'event':'trace_error','description':message.get('description','')[:240]})
 script.on('message',receive)
 script.load()
 write({'event':'trace_attached','pid':pid,'lab_only':True})
 while True:time.sleep(1)
except Exception as e:write({'event':'trace_start_failed','error_type':type(e).__name__,'description':str(e)[:240]})
