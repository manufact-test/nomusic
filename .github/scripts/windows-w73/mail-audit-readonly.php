<?php
declare(strict_types=1);
// W73: remote read-only mail-state audit, no email addresses, ticket text, or secrets leave Hostinger.
ini_set('display_errors', '0');
try {
    if (PHP_SAPI !== 'cli') throw new RuntimeException('cli_required');
    $base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    if (!is_link($base.'/current')) throw new RuntimeException('not_symlink');
    $release=realpath($base.'/current');
    if (!is_string($release) || !str_starts_with($release,$base.'/releases/'))
        throw new RuntimeException('not_release');
    echo 'W73_LIVE_RELEASE='.basename($release)."\n";
    foreach (['src/Application.php','src/Support/SupportService.php',
               'src/Support/SupportAdminView.php','src/Auth/SmtpMailer.php'] as $path) {
        $file=$release.'/'.$path;
        if (!is_file($file)) throw new RuntimeException('missing_live_file');
        echo 'W73_FILE_SHA '.basename($path).' '.hash_file('sha256',$file)."\n";
    }
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    if (($config['environment']??'')!=='production' || ($config['auth_enabled']??false)!==true)
        throw new RuntimeException('not_production');
    $mailer=new \Celikom\Auth\SmtpMailer($config);
    echo 'W73_SMTP_READY='.($mailer->ready()?'YES':'NO')."\n";
    echo 'W73_SMTP_TRANSPORT='.((($config['mail_transport']??'')==='smtp')?'SMTP':'OTHER')."\n";
    echo 'W73_SMTP_SUPPORT_ADDRESS_VALID='.(filter_var($config['mail_from']??'',FILTER_VALIDATE_EMAIL)?'YES':'NO')."\n";
    echo 'W73_SMTP_PORT_ALLOWED='.(in_array((int)($config['mail_port']??0),[465,587],true)?'YES':'NO')."\n";
    $mailHost=strtolower((string)($config['mail_host']??''));
    $mailDomain=strtolower((string)substr(strrchr((string)($config['mail_from']??''),'@')?:'','1'));
    $classify=static function(string $host):string {
        foreach (['hostinger','titan','gmail','google','yandex','mail.ru','zoho',
                  'office365','outlook','brevo','sendgrid','mailgun','postmark',
                  'smtp2go','amazonses'] as $tag) {
            if (str_contains($host,$tag)) return strtoupper(str_replace('.','_',$tag));
        }
        return 'OTHER';
    };
    echo 'W73_SMTP_PROVIDER_CLASS='.$classify($mailHost)."\\n";
    $mx=[];$mxWeights=[];
    $hasMx=$mailDomain!=='' && getmxrr($mailDomain,$mx,$mxWeights);
    echo 'W73_SUPPORT_DOMAIN_MX_PRESENT='.($hasMx?'YES':'NO')."\\n";
    if ($hasMx) {
        $mxClasses=array_unique(array_map($classify,$mx));
        echo 'W73_SUPPORT_DOMAIN_MX_CLASS='.implode('_',$mxClasses)."\\n";
    }
    $pdo=\Celikom\Database\Connection::open($config);
    $query="SELECT t.kind, IF(m.admin_id IS NULL,'notification','admin_reply') AS direction,
                   m.delivery,m.mail_required,COUNT(*) AS count
            FROM support_messages m
            JOIN support_tickets t ON t.id=m.ticket_id
            WHERE m.created_at>=UTC_TIMESTAMP()-INTERVAL 48 HOUR
            GROUP BY t.kind,direction,m.delivery,m.mail_required
            ORDER BY t.kind,direction,m.delivery,m.mail_required";
    foreach ($pdo->query($query)->fetchAll(\PDO::FETCH_ASSOC) as $row) {
        echo 'W73_48H_SUPPORT '.($row['kind']==='song'?'song':'general').' '.
             ($row['direction']==='admin_reply'?'admin_reply':'notification').' '.
             (in_array($row['delivery'],['pending','sending','sent','unknown'],true)?$row['delivery']:'other').' '.
             ((int)$row['mail_required']?'required':'not_required').' count='.(int)$row['count']."\n";
    }
    $q=$pdo->query("SELECT (t.report_json IS NOT NULL) AS has_report, m.delivery,
                          m.mail_required, m.admin_id IS NOT NULL AS reply
                   FROM support_tickets t JOIN support_messages m ON m.ticket_id=t.id
                   WHERE t.kind='general' AND t.created_at>=UTC_TIMESTAMP()-INTERVAL 48 HOUR
                   ORDER BY m.id DESC LIMIT 12");
    $n=0;
    foreach ($q->fetchAll(\PDO::FETCH_ASSOC) as $row) {
        echo 'W73_RECENT_GENERAL_'.(++$n).' snapshot='.(($row['has_report'])?'yes':'no').
             ' delivery='.(in_array($row['delivery'],['pending','sending','sent','unknown'],true)?$row['delivery']:'other').
             ' required='.(($row['mail_required'])?'yes':'no').' reply='.(($row['reply'])?'yes':'no')."\n";
    }
    echo "W73_LIVE_AUDIT_READONLY_PASS\n";
} catch (\Throwable $e) {
    // Do not leak DB, SMTP, account, or filesystem exception strings into CI logs.
    fwrite(STDERR,"W73_LIVE_AUDIT_FAILED\n");
    exit(1);
}
