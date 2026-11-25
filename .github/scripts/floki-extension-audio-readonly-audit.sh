#!/bin/bash
# Bounded read-only host/audio audit. No config, account, trial or release writes.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 && $# == 0 ]] || { echo AUDIO_AUDIT_ROOT_NO_ARGS_REQUIRED; exit 64; }
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
python3 - <<'PY_AUDIO_SETTINGS'
import glob,hashlib,json,os,re,subprocess,time
from pathlib import Path
def emit(kind,**data):
    print(json.dumps({'check':kind,**data},sort_keys=True),flush=True)
emit('audio_audit_start',at=int(time.time()),read_only=True)
app=Path('/srv/celikom/app/staging-20261122')
expected={'src/Http/AudioController.php':'d49a69e556635b29e179f261508be567ec3f2eb6',
 'src/Http/Response.php':'6757ef9500a44d0ad89f480b5d4dbbae9271fa99',
 'src/Entitlement/AudioAccessService.php':'a64a9bd387bbc182686334e3cee064ce9ef5cf13',
 'src/Http/ByteRange.php':'bfdc05ba8adb0ca20177523c73aad324ecfa9b3b'}
for name,want in expected.items():
    p=app/name
    if not p.is_file():
        emit('deployed_source',file=name,present=False);continue
    b=p.read_bytes()
    sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    emit('deployed_source',file=name,baseline_match=sha==want,git_blob=sha,mode=oct(p.stat().st_mode&0o777))
emit('host_load',load=[float(v) for v in Path('/proc/loadavg').read_text().split()[:3]])
mem={}
for line in Path('/proc/meminfo').read_text().splitlines():
    k,_,v=line.partition(':')
    if k in {'MemAvailable','MemTotal','SwapFree','SwapTotal'}:mem[k]=int(v.strip().split()[0])
emit('host_memory_kib',**mem)
fs=os.statvfs('/srv/celikom');emit('host_disk',available_bytes=fs.f_bavail*fs.f_frsize)
for prefix in ['php-fpm','nginx']:
    count=rss=0
    for f in glob.glob('/proc/[0-9]*/comm'):
        try:
            if not Path(f).read_text().strip().startswith(prefix):continue
            count+=1
            for line in Path(f).with_name('status').read_text().splitlines():
                if line.startswith('VmRSS:'):rss+=int(line.split()[1])
        except (OSError,ValueError):pass
    emit('host_workers',name=prefix,count=count,rss_kib=rss)
allowed={'worker_processes','worker_connections','sendfile','tcp_nopush','tcp_nodelay','keepalive_timeout',
 'fastcgi_buffering','fastcgi_request_buffering','fastcgi_buffers','fastcgi_buffer_size',
 'fastcgi_busy_buffers_size','fastcgi_max_temp_file_size','fastcgi_read_timeout','fastcgi_send_timeout',
 'fastcgi_pass','gzip','limit_rate','limit_rate_after','limit_req','limit_conn','output_buffers'}
r=subprocess.run(['nginx','-T'],capture_output=True,text=True,timeout=20)
emit('nginx_syntax',ok=r.returncode==0)
section=''
for line in r.stdout.splitlines():
    if line.startswith('# configuration file '):section=line[len('# configuration file '):].rstrip(':')
    if not section.startswith('/etc/nginx/'):continue
    m=re.fullmatch(r'\s*([a-z_]+)\s+([^;{}\r\n]{1,160});\s*(?:#.*)?',line)
    if m and m[1] in allowed:emit('nginx_directive',scope='api' if section.endswith('/celikom-api-https') else section.removeprefix('/etc/nginx/'),name=m[1],value=m[2].strip())
for path in sorted(glob.glob('/etc/php/*/fpm/php.ini')+glob.glob('/etc/php/*/fpm/pool.d/*.conf')):
    for line in Path(path).read_text().splitlines():
        m=re.fullmatch(r'\s*((?:php_admin_value\[)?(?:output_buffering|implicit_flush|zlib.output_compression|memory_limit|max_execution_time)\]?|pm(?:\.max_children|\.max_requests|\.start_servers|\.min_spare_servers|\.max_spare_servers)?|request_terminate_timeout)\s*=\s*([A-Za-z0-9_. -]{1,80})\s*',line)
        if m:emit('fpm_setting',scope=Path(path).parent.name,name=m[1],value=m[2].strip())
PY_AUDIO_SETTINGS
php <<'PHP_AUDIO_PROBE'
<?php
declare(strict_types=1);
ini_set('display_errors','0');ini_set('log_errors','0');
function auditEmit(string $name,array $data=[]):void{echo json_encode(['check'=>$name]+$data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES),PHP_EOL;}
function auditCheck(bool $ok,string $reason):void{if(!$ok)throw new RuntimeException($reason);}
$pdo=null;
try{
 auditCheck(extension_loaded('curl'),'curl_required');
 require '/srv/celikom/app/staging-20261122/bootstrap.php';
 $config=require '/srv/celikom/app/staging-20261122/config/app.php';
 $pdo=Celikom\Database\Connection::open($config);
 $pdo->exec('SET TRANSACTION READ ONLY');$pdo->beginTransaction();
 auditCheck($pdo->query('SELECT DATABASE()')->fetchColumn()==='celikom_cutover_20261124','database_mismatch');
 $access=new Celikom\Entitlement\AudioAccessService($pdo,(bool)($config['paid_entitlement_enabled']??false));
 $session=null;
 foreach($pdo->query('SELECT id FROM user_sessions WHERE revoked_at IS NULL AND refresh_expires_at>UTC_TIMESTAMP(6) ORDER BY id DESC LIMIT 100')->fetchAll(PDO::FETCH_COLUMN)as$id){
  if($access->allowed((int)$id)){$session=(int)$id;break;}
 }
 auditCheck($session!==null,'existing_authorized_session_required');
 $row=(new Celikom\Repositories\PdoCatalogRepository($pdo))->findActive('yandex','144530503');
 auditCheck(is_array($row)&&$row['mime_type']==='audio/mpeg'&&(int)$row['size_bytes']>589824,'au_approved_mp3_required');
 auditCheck(is_dir($config['storage_path']),'existing_storage_required');
 $storage=new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
 $tokens=new Celikom\Application\AudioTokenService($config['audio_signing_key'],(int)$config['audio_token_ttl']);
 auditEmit('audio_sample',['track_id'=>'144530503','size_bytes'=>(int)$row['size_bytes'],'duration_ms'=>(int)$row['duration_ms'],'existing_session'=>true,'db_transaction_read_only'=>true]);
 $deadline=microtime(true)+180;$allVerified=true;$completed=0;
 foreach([1,2]as$round)foreach(['loopback','public_dns']as$route)foreach([[0,65535],[0,524287],[65536,131071],[65536,589823]]as[$from,$last]){
  $remaining=(int)(($deadline-microtime(true))*1000);if($remaining<1000)break 3;
  $last=min($last,(int)$row['size_bytes']-1);$length=$last-$from+1;
  $f=$storage->openStream($row['storage_key']);auditCheck(fseek($f,$from)===0,'sample_seek_failed');
  $expected=hash_init('sha256');$left=$length;
  while($left>0){$chunk=fread($f,min(65536,$left));auditCheck(is_string($chunk)&&$chunk!=='','sample_read_failed');hash_update($expected,$chunk);$left-=strlen($chunk);}fclose($f);$expected=hash_final($expected);
  $expires=time()+min(120,$tokens->ttl);
  $query=http_build_query(['expires'=>$expires,'token'=>$tokens->sign((int)$row['replacement_id'],(int)$row['version'],$expires,$session),'sid'=>$session],arg_separator:'&',encoding_type:PHP_QUERY_RFC3986);
  $url='https://api.celikom.com/api/v1/audio/'.(int)$row['replacement_id'].'?'.$query;
  $started=microtime(true);$bytes=0;$first=null;$progress=[];$headers=[];$digest=hash_init('sha256');$next=65536;
  $ch=curl_init($url);
  $options=[CURLOPT_FOLLOWLOCATION=>false,CURLOPT_PROXY=>'',CURLOPT_CONNECTTIMEOUT_MS=>4000,CURLOPT_TIMEOUT_MS=>min(12000,$remaining),
   CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_USERAGENT=>'CELIKOM-Audio-Readonly-Audit/1',
   CURLOPT_HTTPHEADER=>['Range: bytes='.$from.'-'.$last,'Accept-Encoding: identity'],
   CURLOPT_HEADERFUNCTION=>static function($ch,string $line)use(&$headers):int{$parts=explode(':',$line,2);if(count($parts)===2)$headers[strtolower(trim($parts[0]))]=trim($parts[1]);return strlen($line);},
   CURLOPT_WRITEFUNCTION=>static function($ch,string $chunk)use(&$bytes,&$first,&$progress,&$next,$started,$length,$digest):int{
    $n=strlen($chunk);if($bytes+$n>$length)return 0;
    $first??=round((microtime(true)-$started)*1000,2);$bytes+=$n;hash_update($digest,$chunk);
    while($bytes>=$next){$progress[]=['bytes'=>$bytes,'ms'=>round((microtime(true)-$started)*1000,2)];$next+=65536;}return $n;
   }];
  if($route==='loopback')$options[CURLOPT_RESOLVE]=['api.celikom.com:443:127.0.0.1'];
  curl_setopt_array($ch,$options);$ok=curl_exec($ch);$info=curl_getinfo($ch);$errno=curl_errno($ch);curl_close($ch);
  $actual=hash_final($digest);
  $verified=$ok!==false&&$info['http_code']===206&&$bytes===$length&&hash_equals($expected,$actual)
   &&($headers['content-range']??'')==='bytes '.$from.'-'.$last.'/'.$row['size_bytes']
   &&($headers['etag']??'')==='"'.$row['sha256'].'-'.$row['version'].'"';
  $allVerified=$allVerified&&$verified;$completed++;
  auditEmit('audio_range',['round'=>$round,'route'=>$route,'offset'=>$from,'requested_bytes'=>$length,'received_bytes'=>$bytes,
   'http_status'=>(int)$info['http_code'],'curl_errno'=>$errno,'verified'=>$verified,
   'dns_ms'=>round($info['namelookup_time']*1000,2),'connect_ms'=>round($info['connect_time']*1000,2),
   'ttfb_ms'=>round($info['starttransfer_time']*1000,2),'first_body_ms'=>$first,'total_ms'=>round($info['total_time']*1000,2),
   'progress_64k'=>$progress,'body_sha256'=>$actual,'ip_family'=>str_contains($info['primary_ip'],':')?'ipv6':'ipv4']);
 }
 auditEmit('audio_audit_complete',['requests'=>$completed,'expected_requests'=>16,'all_verified'=>$allVerified&&$completed===16]);
}catch(Throwable $error){
 $safe=['curl_required','database_mismatch','existing_authorized_session_required','au_approved_mp3_required','existing_storage_required','sample_seek_failed','sample_read_failed'];
 auditEmit('audio_audit_failed',['reason'=>in_array($error->getMessage(),$safe,true)?$error->getMessage():'probe_failed']);exit(1);
}finally{if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();}
PHP_AUDIO_PROBE
