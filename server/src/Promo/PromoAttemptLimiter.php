<?php

declare(strict_types=1);
namespace Celikom\Promo;
use PDO;
final class PromoAttemptLimiter
{
    public function __construct(private readonly PDO $pdo,private readonly string $key) {}
    public function allow(int $user,string $device,string $ip): bool
    {
        if(strlen($this->key)<32)throw new \RuntimeException('promo_privacy_key_missing');
        $window=(int)$this->pdo->query('SELECT FLOOR(UNIX_TIMESTAMP(UTC_TIMESTAMP())/900)')->fetchColumn();
        $allowed=true;
        foreach(['account'=>[$user,10],'device'=>[$device,20],'ip'=>[$ip,60]] as $scope=>[$identity,$limit]){
            $hash=hash_hmac('sha256','promo:'.$scope.':'.$identity,$this->key);
            $q=$this->pdo->prepare('INSERT INTO promo_attempt_buckets(identity_hash,window_start,attempts) VALUES (?,?,1) ON DUPLICATE KEY UPDATE attempts=LAST_INSERT_ID(attempts+1)');
            $q->execute([$hash,$window]);
            // Atomic claim: INSERT has 1; UPDATE exposes exactly this request's counter.
            $attempts=$q->rowCount()===1?1:(int)$this->pdo->lastInsertId();
            if($attempts>$limit)$allowed=false;
        }
        return $allowed;
    }
}
