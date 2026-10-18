<?php
declare(strict_types=1);
namespace Celikom\Website;

use RuntimeException;

/**
 * Stage 10 CI-ONLY sealed offsite transport of a COORDINATED CMS restore point.
 *
 * Authenticated XChaCha20-Poly1305 secretstream wraps the encrypted MySQL
 * archive AND the otherwise plaintext content/private-media archive together.
 * The offsite destination contains ONLY one ciphertext file; no unencrypted
 * image, metadata or backup manifest is ever copied there.
 *
 * This is an offline cryptographic drill, not a cloud uploader or production
 * backup service. Export requires two independent 32-byte keys.
 */
final class CmsOffsiteEnvelope
{
    private const MAGIC = "CELIKOM_SITE_OFFSITE_V1\n";
    private const MAX_INPUT = 201_326_592;
    private const CHUNK = 65536;
    private const MAX_FRAME = 100000;
    private const PARTS = 3;

    public static function keyFromEnv(string $fullDbKey):string
    {
        $encoded=getenv('CELIKOM_SITE_OFFSITE_KEY');
        $key=is_string($encoded)?base64_decode($encoded,true):false;
        if (!is_string($key) || strlen($key)!==32 ||
            hash_equals($key,$fullDbKey)) {
            throw new RuntimeException('A separate random 32-byte offsite encryption key is required');
        }
        return $key;
    }

    public static function seal(
        string $manifest,string $fullDbKey,string $offsiteKey,
        string $transportDir,string $publicDir
    ):string {
        self::guard($fullDbKey,$offsiteKey);
        $source=self::privateDir(dirname($manifest),$publicDir);
        $target=self::privateDir($transportDir,$publicDir);
        if ($source===$target) {
            throw new RuntimeException('Offsite ciphertext must be staged separately from plaintext');
        }
        CmsConsistentBackup::inspect($manifest,$fullDbKey,$publicDir);
        $meta=json_decode((string)file_get_contents($manifest),true,32,JSON_THROW_ON_ERROR);
        $items=[
            (string)$meta['full_db']['name'],
            (string)$meta['content_media']['name'],
            basename($manifest),
        ];
        if (count(array_unique($items))!==self::PARTS ||
            !preg_match('/^celikom-restore-point-[a-z0-9-]{12,100}\\.json$/D',$items[2])) {
            throw new RuntimeException('Invalid or overlapping coordinated backup parts');
        }
        $files=[];
        $total=0;
        foreach ($items as $item) {
            $path=$source.'/'.$item;
            if (!self::privateFile($path,$source)) {
                throw new RuntimeException('Backup component escaped its source directory');
            }
            $length=filesize($path);
            if (!is_int($length) || $length<10 || ($total+=$length)>self::MAX_INPUT) {
                throw new RuntimeException('Coordinated archive exceeds sealed transport budget');
            }
            $files[]=['name'=>$item,'bytes'=>$length,'sha256'=>hash_file('sha256',$path)];
        }
        $name='celikom-offsite-'.gmdate('Ymd-His').'-'.bin2hex(random_bytes(12)).'.sbox';
        $tmp=$target.'/.'.$name.'.tmp';
        $final=$target.'/'.$name;
        $fp=fopen($tmp,'xb');
        if ($fp===false) throw new RuntimeException('Cannot open private sealed transport');
        try {
            if (!chmod($tmp,0600)) throw new RuntimeException('Cannot protect ciphertext');
            [$state,$header]=sodium_crypto_secretstream_xchacha20poly1305_init_push($offsiteKey);
            self::writeAll($fp,self::MAGIC.$header);
            self::writeRecord($fp,$state,[
                'kind'=>'header','format'=>1,'files'=>$files
            ]);
            foreach ($files as $index=>$file) {
                $input=fopen($source.'/'.$file['name'],'rb');
                if ($input===false) throw new RuntimeException('Cannot read coordinated backup');
                try {
                    $count=0;
                    $sha=hash_init('sha256');
                    while (!feof($input)) {
                        $chunk=fread($input,self::CHUNK);
                        if ($chunk===false) throw new RuntimeException('Cannot read private backup chunk');
                        if ($chunk==='') {
                            if (!feof($input)) throw new RuntimeException('Unexpected empty backup read');
                            break;
                        }
                        $count+=strlen($chunk);
                        if ($count>$file['bytes']) throw new RuntimeException('Backup changed during encryption');
                        hash_update($sha,$chunk);
                        self::writeRecord($fp,$state,[
                            'kind'=>'part','index'=>$index,'data'=>base64_encode($chunk)
                        ]);
                    }
                    if ($count!==$file['bytes'] ||
                        !hash_equals($file['sha256'],hash_final($sha))) {
                        throw new RuntimeException('Backup modified while sealing');
                    }
                } finally {
                    fclose($input);
                }
            }
            self::writeRecord($fp,$state,['kind'=>'end'],
                SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_FINAL);
            if (!fflush($fp)) throw new RuntimeException('Cannot flush sealed transport');
        } catch (\Throwable $e) {
            fclose($fp);
            @unlink($tmp);
            throw $e;
        }
        fclose($fp);
        if (!rename($tmp,$final)) {
            @unlink($tmp);
            throw new RuntimeException('Cannot publish sealed archive');
        }
        try {
            // Authenticate the transport independently of its original files.
            self::openAndVerify($final,$offsiteKey,null);
        } catch (\Throwable $e) {
            @unlink($final);
            throw $e;
        }
        return $final;
    }

    /**
     * Authenticated verification without producing decrypted output.
     * Returns safe metadata only, never image bytes, admin hashes or filenames.
     */
    public static function inspect(string $path,string $key):array
    {
        self::requireCi();
        self::checkKey($key);
        return self::openAndVerify($path,$key,null);
    }

    /**
     * Unseal into a FRESH private directory and validate the restored full
     * MySQL+content/media pair using the separately held DB encryption key.
     * On any authentication/format/media failure, securely remove the stage
     * files (unlink, not a secure-erasure promise).
     */
    public static function unseal(
        string $sealed,string $fullDbKey,string $offsiteKey,
        string $restoreParent,string $publicDir
    ):array {
        self::guard($fullDbKey,$offsiteKey);
        $parent=self::privateDir($restoreParent,$publicDir);
        $dir=$parent.'/celikom-offsite-unsealed-'.bin2hex(random_bytes(10));
        if (!mkdir($dir,0700)) throw new RuntimeException('Cannot allocate private restore area');
        try {
            $report=self::openAndVerify($sealed,$offsiteKey,$dir);
            if ($report['files']!==self::PARTS || !is_string($report['manifest'])) {
                throw new RuntimeException('Incomplete offsite transport');
            }
            $manifest=$dir.'/'.$report['manifest'];
            $verified=CmsConsistentBackup::inspect($manifest,$fullDbKey,$publicDir);
            if (($verified['consistent']??false)!==true) {
                throw new RuntimeException('Restored CMS backups differ');
            }
            return ['manifest'=>$manifest,'report'=>$verified,'encrypted_transport'=>true];
        } catch (\Throwable $e) {
            self::clearStage($dir);
            throw $e;
        }
    }

    private static function openAndVerify(string $path,string $key,?string $dest):array
    {
        self::requireCi();
        self::checkKey($key);
        $dir=realpath(dirname($path));
        if (!is_string($dir) || !self::privateFile($path,$dir) ||
            !preg_match('/^celikom-offsite-[0-9]{8}-[0-9]{6}-[a-f0-9]{24}\\.sbox$/D',basename($path))) {
            throw new RuntimeException('Sealed archive path or permissions invalid');
        }
        $fp=fopen($path,'rb');
        if ($fp===false) throw new RuntimeException('Cannot open sealed archive');
        $handles=[];
        try {
            if (self::readExact($fp,strlen(self::MAGIC))!==self::MAGIC) {
                throw new RuntimeException('Offsite archive magic mismatch');
            }
            $header=self::readExact($fp,SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_HEADERBYTES);
            $state=sodium_crypto_secretstream_xchacha20poly1305_init_pull($header,$key);
            $files=null;
            $expected=0;
            $part=0;
            $bytes=0;
            $hash=hash_init('sha256');
            $ended=false;
            while (true) {
                $lengthBytes=fread($fp,4);
                if ($lengthBytes==='') break;
                if ($lengthBytes===false || strlen($lengthBytes)!==4) {
                    throw new RuntimeException('Truncated sealed transport frame');
                }
                $size=unpack('N',$lengthBytes)[1];
                if ($size<17 || $size>self::MAX_FRAME) {
                    throw new RuntimeException('Sealed frame size invalid');
                }
                $cipher=self::readExact($fp,$size);
                $plain=sodium_crypto_secretstream_xchacha20poly1305_pull($state,$cipher);
                if (!is_array($plain)) throw new RuntimeException('Offsite authentication failed');
                [$json,$tag]=$plain;
                $record=json_decode($json,true,16,JSON_THROW_ON_ERROR);
                if (!is_array($record)) throw new RuntimeException('Invalid offsite record');
                if ($files===null) {
                    if ($tag!==SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_MESSAGE ||
                        array_keys($record)!==['kind','format','files'] ||
                        $record['kind']!=='header' || $record['format']!==1 ||
                        !is_array($record['files']) || count($record['files'])!==self::PARTS) {
                        throw new RuntimeException('Offsite encrypted header invalid');
                    }
                    $files=$record['files'];
                    $names=[];
                    $total=0;
                    foreach ($files as $i=>$item) {
                        if (!is_array($item) ||
                            array_keys($item)!==['name','bytes','sha256'] ||
                            !is_string($item['name']) ||
                            !preg_match('/^celikom-[a-z0-9-]{12,100}\\.(?:json|sbox)$/D',$item['name']) ||
                            !is_int($item['bytes']) || $item['bytes']<10 ||
                            ($total+=$item['bytes'])>self::MAX_INPUT ||
                            !is_string($item['sha256']) ||
                            !preg_match('/^[a-f0-9]{64}$/D',$item['sha256']) ||
                            in_array($item['name'],$names,true)) {
                            throw new RuntimeException('Untrusted offsite file inventory');
                        }
                        $names[]=$item['name'];
                    }
                    if (!str_ends_with($files[0]['name'],'.sbox') ||
                        !str_ends_with($files[1]['name'],'.json') ||
                        !preg_match('/^celikom-restore-point-[a-z0-9-]{12,100}\\.json$/D',$files[2]['name'])) {
                        throw new RuntimeException('Unrecognized coordinated restore inventory');
                    }
                    $expected=$files[0]['bytes'];
                    if ($dest!==null) $handles[0]=self::create($dest.'/'.$files[0]['name']);
                    continue;
                }
                if (($record['kind']??null)==='part' &&
                    $tag===SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_MESSAGE &&
                    array_keys($record)===['kind','index','data'] &&
                    ($record['index']??null)===$part &&
                    is_string($record['data']??null)) {
                    $chunk=base64_decode($record['data'],true);
                    if (!is_string($chunk) || strlen($chunk)<1 ||
                        strlen($chunk)>self::CHUNK || $bytes+strlen($chunk)>$expected) {
                        throw new RuntimeException('Untrusted offsite payload length');
                    }
                    hash_update($hash,$chunk);
                    if ($dest!==null) self::writeAll($handles[$part],$chunk);
                    $bytes+=strlen($chunk);
                    if ($bytes===$expected) {
                        if (!hash_equals($files[$part]['sha256'],hash_final($hash))) {
                            throw new RuntimeException('Authenticated file digest differs');
                        }
                        if ($dest!==null) {
                            if (!fflush($handles[$part])) throw new RuntimeException('Cannot flush decrypted file');
                            fclose($handles[$part]);
                            unset($handles[$part]);
                        }
                        ++$part;
                        $bytes=0;
                        $hash=hash_init('sha256');
                        if ($part<self::PARTS) {
                            $expected=$files[$part]['bytes'];
                            if ($dest!==null) $handles[$part]=self::create($dest.'/'.$files[$part]['name']);
                        }
                    }
                    continue;
                }
                if (($record['kind']??null)==='end' && $part===self::PARTS &&
                    array_keys($record)===['kind'] &&
                    $tag===SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_FINAL &&
                    fread($fp,1)==='' && feof($fp)) {
                    $ended=true;
                    break;
                }
                throw new RuntimeException('Incomplete or inconsistent sealed archive');
            }
            if (!$ended) throw new RuntimeException('Missing authenticated offsite final trailer');
            return ['encrypted'=>true,'files'=>self::PARTS,
                'manifest'=>$files[2]['name']];
        } finally {
            foreach ($handles as $handle) {
                if (is_resource($handle)) fclose($handle);
            }
            fclose($fp);
        }
    }

    private static function create(string $path):mixed
    {
        $fp=fopen($path,'xb');
        if ($fp===false) throw new RuntimeException('Refusing to overwrite decrypted content');
        if (!chmod($path,0600)) {
            fclose($fp);
            throw new RuntimeException('Decrypted file permission error');
        }
        return $fp;
    }

    private static function clearStage(string $dir):void
    {
        if (is_link($dir) || !is_dir($dir)) return;
        foreach (scandir($dir) as $file) {
            if ($file==='.' || $file==='..') continue;
            $path=$dir.'/'.$file;
            if (is_file($path) && !is_link($path)) @unlink($path);
        }
        @rmdir($dir);
    }

    private static function guard(string $dbKey,string $offsiteKey):void
    {
        self::requireCi();
        self::checkKey($dbKey);
        self::checkKey($offsiteKey);
        if (hash_equals($dbKey,$offsiteKey)) {
            throw new RuntimeException('Offsite and DB backup keys cannot be reused');
        }
    }
    private static function checkKey(string $key):void
    {
        if (strlen($key)!==SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_KEYBYTES) {
            throw new RuntimeException('Expected independent 32-byte encryption key');
        }
    }
    private static function requireCi():void
    {
        if (getenv('CI')!=='true' ||
            getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1') {
            throw new RuntimeException('Offsite envelope is only available in isolated CI');
        }
    }
    private static function privateDir(string $path,string $public):string
    {
        $dir=realpath($path);
        $web=realpath($public);
        if (!is_string($dir) || !is_string($web) || !is_dir($dir) ||
            !is_dir($web) || is_link($path) || $dir===$web ||
            str_starts_with($dir,$web.'/') || str_starts_with($web,$dir.'/') ||
            (fileperms($dir)&0077)!==0) {
            throw new RuntimeException('Offsite backup requires independent private directories');
        }
        return $dir;
    }
    private static function privateFile(string $path,string $dir):bool
    {
        clearstatcache(true,$path);
        return is_file($path) && !is_link($path) &&
            realpath($path)===$path && dirname($path)===$dir &&
            (fileperms($path)&0077)===0 &&
            (fileperms($path)&0170000)===0100000 &&
            (stat($path)['nlink']??0)===1;
    }
    private static function writeRecord(mixed $fp,string &$state,array $record,int $tag=SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_MESSAGE):void
    {
        $raw=json_encode($record,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES);
        $cipher=sodium_crypto_secretstream_xchacha20poly1305_push($state,$raw,'',$tag);
        if (strlen($cipher)>self::MAX_FRAME) throw new RuntimeException('Offsite chunk exceeds frame budget');
        self::writeAll($fp,pack('N',strlen($cipher)).$cipher);
    }
    private static function writeAll(mixed $fp,string $bytes):void
    {
        $at=0;$length=strlen($bytes);
        while ($at<$length) {
            $sent=fwrite($fp,substr($bytes,$at));
            if (!is_int($sent) || $sent<1) throw new RuntimeException('Incomplete sealed stream write');
            $at+=$sent;
        }
    }
    private static function readExact(mixed $fp,int $length):string
    {
        $buffer='';
        while (strlen($buffer)<$length) {
            $next=fread($fp,$length-strlen($buffer));
            if (!is_string($next) || $next==='') throw new RuntimeException('Truncated sealed stream');
            $buffer.=$next;
        }
        return $buffer;
    }
}
