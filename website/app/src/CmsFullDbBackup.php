<?php
declare(strict_types=1);
namespace Celikom\Website;

use PDO;
use RuntimeException;

/**
 * CLI-only, encrypted logical backup of the ENTIRE dedicated website CMS DB.
 * Unlike CmsBackup (content + images), this includes administrator hashes,
 * audit records and throttling buckets; plaintext MUST NEVER touch the disk.
 *
 * Key: an independent random 32-byte secret as strict base64, supplied via
 * CELIKOM_SITE_FULL_BACKUP_KEY (not in code, GitHub, arguments or log output).
 * XChaCha20-Poly1305 secretstream authenticates every record and final EOF.
 * Does NOT back up external private image files. Stage 10 still needs a
 * verified full recovery drill and hosting-specific rollback.
 */
final class CmsFullDbBackup
{
    private const MAGIC = "CELIKOM_ENCRYPTED_SITE_DB_V1\n";
    private const MAX_RECORD = 8_500_000;
    private const MAX_ROWS = 100_000;
    private const MAX_BYTES = 134_217_728;
    private const TABLES = [
        'admin_users', 'media_assets', 'faq_categories', 'faq_items',
        'site_content', 'site_settings', 'content_revisions', 'site_state',
        'content_drafts', 'login_rate_limits', 'audit_log',
    ];

    public static function keyFromEnv(): string
    {
        $encoded=getenv('CELIKOM_SITE_FULL_BACKUP_KEY');
        $key=is_string($encoded)?base64_decode($encoded,true):false;
        if(!is_string($key) || strlen($key)!==32 ||
            !function_exists('sodium_crypto_secretstream_xchacha20poly1305_init_push')) {
            throw new RuntimeException('Independent 32-byte full-backup encryption key is required');
        }
        return $key;
    }

    public static function export(
        PDO $pdo,string $targetDir,string $publicDir,string $key
    ):string {
        self::checkKey($key);
        $out=realpath($targetDir);
        $public=realpath($publicDir);
        if(!is_string($out)||!is_string($public)||!is_dir($out)||
            !is_dir($public)||is_link($targetDir)||$out===$public||
            str_starts_with($out,$public.'/')||
            str_starts_with($public,$out.'/')||
            (fileperms($out)&0077)!==0) {
            throw new RuntimeException('Full backup needs a separate owner-only private directory');
        }
        $filename='celikom-full-db-'.gmdate('Ymd-His').'-'.bin2hex(random_bytes(8)).'.sbox';
        $temp=$out.'/.'.$filename.'.tmp';
        $final=$out.'/'.$filename;
        $fp=@fopen($temp,'x+b');
        if($fp===false)throw new RuntimeException('Cannot allocate secure backup');
        try {
            if(!chmod($temp,0600))throw new RuntimeException('Cannot protect backup file');
            [$state,$header]=sodium_crypto_secretstream_xchacha20poly1305_init_push($key);
            self::writeAll($fp,self::MAGIC.$header);
            $pdo->exec('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
            $pdo->beginTransaction();
            try {
                $counts=array_fill_keys(self::TABLES,0);
                self::writeRecord($fp,$state,[
                    'kind'=>'header','format'=>1,'tables'=>self::TABLES,
                ]);
                $total=0;
                foreach(self::TABLES as $table) {
                    $result=$pdo->query('SELECT * FROM '.$table);
                    while(($row=$result->fetch(PDO::FETCH_ASSOC))!==false) {
                        if(++$total>self::MAX_ROWS) {
                            throw new RuntimeException('Backup row budget exceeded');
                        }
                        self::writeRecord($fp,$state,[
                            'kind'=>'row','table'=>$table,'data'=>$row,
                        ]);
                        ++$counts[$table];
                    }
                }
                self::writeRecord($fp,$state,[
                    'kind'=>'final','counts'=>$counts,
                ],SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_FINAL);
                if(!fflush($fp) || ftell($fp)>self::MAX_BYTES) {
                    throw new RuntimeException('Encrypted CMS DB backup exceeds size limit');
                }
                $pdo->commit();
            } catch(\Throwable $error) {
                if($pdo->inTransaction())$pdo->rollBack();
                throw $error;
            }
        } catch(\Throwable $error) {
            fclose($fp);
            @unlink($temp);
            throw $error;
        }
        fclose($fp);
        if(!rename($temp,$final)) {
            @unlink($temp);
            throw new RuntimeException('Cannot finalize encrypted site backup');
        }
        // Verify the same authenticated stream before reporting success.
        try {
            self::inspect($final,$key);
        } catch(\Throwable $error) {
            @unlink($final);
            throw $error;
        }
        return $final;
    }

    /**
     * Verify stream authentication, exact tables, counts and final record.
     * Optional callback can replay rows into a DISTINCT CI-only DB in a
     * separately designed restoration tool; this method makes no DB writes.
     *
     * @return array{tables:array<string,int>,total_rows:int,encrypted:bool}
     */
    public static function inspect(string $path,string $key,?callable $onRow=null):array
    {
        self::checkKey($key);
        if(!is_file($path)||is_link($path)||
            (fileperms($path)&0077)!==0||
            ($size=filesize($path))===false ||
            $size<strlen(self::MAGIC)+24+8||$size>self::MAX_BYTES) {
            throw new RuntimeException('Invalid encrypted site backup');
        }
        $fp=fopen($path,'rb');
        if($fp===false)throw new RuntimeException('Cannot open encrypted backup');
        try {
            $prefix=self::readExact($fp,strlen(self::MAGIC));
            if(!hash_equals(self::MAGIC,$prefix)) {
                throw new RuntimeException('Encrypted site backup format mismatch');
            }
            $header=self::readExact($fp,
                SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_HEADERBYTES);
            $state=sodium_crypto_secretstream_xchacha20poly1305_init_pull($header,$key);
            $counts=array_fill_keys(self::TABLES,0);
            $total=0;
            $stage='header';
            $ended=false;
            while(!feof($fp)) {
                $four=fread($fp,4);
                if($four==='')break;
                if(!is_string($four)||strlen($four)!==4) {
                    throw new RuntimeException('Truncated encrypted record framing');
                }
                $length=unpack('N',$four)[1];
                if($length<17 || $length>self::MAX_RECORD) {
                    throw new RuntimeException('Encrypted record length out of bounds');
                }
                $raw=self::readExact($fp,$length);
                $decrypted=sodium_crypto_secretstream_xchacha20poly1305_pull($state,$raw);
                if(!is_array($decrypted)) {
                    throw new RuntimeException('Encrypted record authentication failed');
                }
                [$json,$tag]=$decrypted;
                $record=json_decode($json,true,512,JSON_THROW_ON_ERROR);
                if(!is_array($record))throw new RuntimeException('Invalid backup record');
                if($stage==='header') {
                    if($tag!==SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_MESSAGE ||
                        $record!==['kind'=>'header','format'=>1,'tables'=>self::TABLES]) {
                        throw new RuntimeException('Invalid encrypted header record');
                    }
                    $stage='rows';
                    continue;
                }
                if(($record['kind']??null)==='row' && $stage==='rows') {
                    $table=$record['table']??null;
                    if($tag!==SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_MESSAGE ||
                        !is_string($table)||!array_key_exists($table,$counts)||
                        !is_array($record['data']??null)||++$total>self::MAX_ROWS) {
                        throw new RuntimeException('Invalid encrypted database row');
                    }
                    ++$counts[$table];
                    if($onRow!==null)$onRow($table,$record['data']);
                    continue;
                }
                if(($record['kind']??null)==='final' && $stage==='rows' &&
                    $tag===SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_FINAL &&
                    ($record['counts']??null)===$counts && feof($fp)) {
                    $ended=true;
                    break;
                }
                throw new RuntimeException('Missing valid authenticated backup trailer');
            }
            if(!$ended)throw new RuntimeException('Encrypted backup is truncated or incomplete');
            return ['tables'=>$counts,'total_rows'=>$total,'encrypted'=>true];
        } finally {
            fclose($fp);
        }
    }

    private static function writeRecord(
        mixed $fp,string &$state,array $record,int $tag=SODIUM_CRYPTO_SECRETSTREAM_XCHACHA20POLY1305_TAG_MESSAGE
    ):void {
        $json=json_encode($record,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
        if(strlen($json)>self::MAX_RECORD-17)throw new RuntimeException('Database row too large');
        $cipher=sodium_crypto_secretstream_xchacha20poly1305_push($state,$json,'',$tag);
        self::writeAll($fp,pack('N',strlen($cipher)).$cipher);
        if(ftell($fp)>self::MAX_BYTES)throw new RuntimeException('Database backup too large');
    }

    private static function writeAll(mixed $fp,string $bytes):void
    {
        for($offset=0,$size=strlen($bytes);$offset<$size;) {
            $written=fwrite($fp,substr($bytes,$offset));
            if(!is_int($written)||$written<1)throw new RuntimeException('Backup write interrupted');
            $offset+=$written;
        }
    }

    private static function readExact(mixed $fp,int $size):string
    {
        $buffer='';
        while(strlen($buffer)<$size) {
            $bytes=fread($fp,$size-strlen($buffer));
            if(!is_string($bytes)||$bytes==='') {
                throw new RuntimeException('Truncated encrypted site backup');
            }
            $buffer.=$bytes;
        }
        return $buffer;
    }

    private static function checkKey(string $key):void
    {
        if(strlen($key)!==32 ||
            !function_exists('sodium_crypto_secretstream_xchacha20poly1305_init_push')) {
            throw new RuntimeException('Missing encrypted backup primitive or valid key');
        }
    }
}
