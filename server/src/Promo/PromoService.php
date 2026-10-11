<?php

declare(strict_types=1);

namespace Celikom\Promo;

use PDO;
use Celikom\Incident\IncidentService;
use Celikom\Entitlement\EntitlementService;

final class PromoService
{
    public function __construct(private readonly PDO $pdo) {}
    public static function code(mixed $value): string
    {
        if (!is_string($value) || !preg_match('/^[A-Za-z0-9_-]{8,64}$/D',trim($value))) throw new \InvalidArgumentException('invalid_promo');
        return strtoupper(trim($value));
    }
    private function owner(int $id): void
    {
        $q=$this->pdo->prepare("SELECT id FROM admins WHERE id=? AND role='owner' AND enabled=1");$q->execute([$id]);
        if (!$q->fetchColumn()) throw new \DomainException('forbidden');
    }
    public function create(int $actor,array $input): int
    {
        $this->owner($actor); $code=self::code($input['code']??null); $title=$input['title']??null;
        if (!is_string($title) || trim($title)==='' || !preg_match('//u',$title) || preg_match_all('/./us',$title)>120
            || !preg_match('/^[a-f0-9]{64}$/D',$input['request_key']??'')) throw new \InvalidArgumentException('invalid_promo');
        $forever=($input['forever']??'0')==='1';
        if ($forever && ($input['confirm_forever']??'')!=='1') throw new \InvalidArgumentException('confirm_forever_required');
        $values=[];
        foreach (['discount_percent'=>100,'duration_days'=>3660,'max_activations'=>1000000] as $k=>$max) {
            if($k==='duration_days' && $forever){$values[$k]=null;continue;}
            $v=$input[$k]??null;
            if (!(is_int($v) || (is_string($v) && ctype_digit($v))) || (int)$v<1 || (int)$v>$max) throw new \InvalidArgumentException('invalid_promo');
            $values[$k]=(int)$v;
        }
        if($forever && $values['discount_percent']!==100)throw new \InvalidArgumentException('invalid_promo');
        $values['forever']=$forever?1:0;
        $deadline=null;
        if (($input['activation_window']??null)==='fixed') {
            $date=\DateTimeImmutable::createFromFormat('!Y-m-d\TH:i',(string)($input['activation_deadline']??''),new \DateTimeZone('UTC'));
            if (!$date || $date->format('Y-m-d\TH:i')!==$input['activation_deadline']) throw new \InvalidArgumentException('invalid_promo');
            $deadline=$date->format('Y-m-d H:i:s.000000');
        } elseif (($input['activation_window']??null)!=='unlimited') throw new \InvalidArgumentException('invalid_promo');
        $expected=['code'=>$code,'title'=>trim($title)]+$values+['activation_deadline'=>$deadline,'created_by'=>$actor];
        if($this->pdo->inTransaction())throw new \LogicException('transaction_already_active');$this->pdo->beginTransaction();
        try {
            $q=$this->pdo->prepare('SELECT * FROM promo_codes WHERE request_key=? FOR UPDATE');$q->execute([$input['request_key']]);
            if ($row=$q->fetch(PDO::FETCH_ASSOC)) {
                foreach($expected as $k=>$v) if((string)$row[$k]!== (string)$v) throw new \DomainException('promo_conflict');
                $this->pdo->commit();return (int)$row['id'];
            }
            if ($deadline!==null && $deadline<=(string)$this->pdo->query('SELECT UTC_TIMESTAMP(6)')->fetchColumn()) throw new \InvalidArgumentException('invalid_promo');
            $q=$this->pdo->prepare('INSERT INTO promo_codes(code,title,discount_percent,duration_days,max_activations,forever,activation_deadline,request_key,created_by) VALUES (?,?,?,?,?,?,?,?,?)');
            $q->execute([$code,trim($title),$values['discount_percent'],$values['duration_days'],$values['max_activations'],$values['forever'],$deadline,$input['request_key'],$actor]);
            $id=(int)$this->pdo->lastInsertId();$this->audit($actor,'promo_created',$id,$values+['activation_deadline'=>$deadline]);
            $this->pdo->commit();return $id;
        } catch (\Throwable $e) {if($this->pdo->inTransaction())$this->pdo->rollBack();if($e instanceof \PDOException && $e->getCode()==='23000') throw new \DomainException('promo_conflict');throw $e;}
    }
    public function redeem(int $userId,string $text): array
    {
        $code=self::code($text);if($this->pdo->inTransaction())throw new \LogicException('transaction_already_active');$this->pdo->beginTransaction();
        try {
            // Shared account lock serializes different codes and existing TrialService activation.
            $q=$this->pdo->prepare('SELECT u.status,e.verified_at FROM users u LEFT JOIN user_email_security e ON e.user_id=u.id WHERE u.id=? FOR UPDATE');$q->execute([$userId]);$user=$q->fetch(PDO::FETCH_ASSOC);
            if(!$user || $user['status']!=='active' || $user['verified_at']===null) throw new \DomainException('account_unavailable');
            $q=$this->pdo->prepare('SELECT * FROM promo_codes WHERE code=? FOR UPDATE');$q->execute([$code]);$promo=$q->fetch(PDO::FETCH_ASSOC);
            if(!$promo) throw new \DomainException('promo_unavailable');
            $q=$this->pdo->prepare('SELECT id,revoked_at FROM promo_redemptions WHERE promo_id=? AND user_id=?');$q->execute([$promo['id'],$userId]);
            if($r=$q->fetch(PDO::FETCH_ASSOC)) {$this->pdo->commit();return ['redemption_id'=>(int)$r['id'],'already_activated'=>true,'revoked'=>$r['revoked_at']!==null,'entitlement'=>(new EntitlementService($this->pdo))->check($userId)->json()];}
            $now=(string)$this->pdo->query('SELECT UTC_TIMESTAMP(6)')->fetchColumn();
            if($promo['revoked_at']!==null || (int)$promo['used_activations']>=(int)$promo['max_activations'] || ($promo['activation_deadline']!==null && $promo['activation_deadline']<=$now)) throw new \DomainException('promo_unavailable');
            if((int)$promo['discount_percent']!==100) throw new \DomainException('promo_payment_pending');
            $previous=(new PromoAccessService($this->pdo))->best($userId);
            if($previous!==null && $previous['until']===null)throw new \DomainException('promo_lifetime_active');
            $forever=(int)$promo['forever']===1;
            $from=$forever?$now:max($now,$previous['until']??$now);
            $until=$forever?null:IncidentService::date(IncidentService::micros($from)+(int)$promo['duration_days']*86400000000);
            $q=$this->pdo->prepare("INSERT INTO entitlement_ledger(user_id,source,reason,valid_from,valid_until) VALUES (?,'promo','owner_promo_free',?,?)");$q->execute([$userId,$from,$until]);$ledger=(int)$this->pdo->lastInsertId();
            $q=$this->pdo->prepare('INSERT INTO promo_redemptions(promo_id,user_id,ledger_id,parent_ledger_id,duration_days,forever,valid_from,valid_until,activated_at) VALUES (?,?,?,?,?,?,?,?,?)');
            $q->execute([$promo['id'],$userId,$ledger,($forever?null:($previous['ledger_id']??null)),$promo['duration_days'],$promo['forever'],$from,$until,$now]);$id=(int)$this->pdo->lastInsertId();
            $q=$this->pdo->prepare('UPDATE promo_codes SET used_activations=used_activations+1 WHERE id=? AND used_activations<max_activations');$q->execute([$promo['id']]);
            if($q->rowCount()!==1) throw new \DomainException('promo_unavailable');
            $this->audit((int)$promo['created_by'],'promo_redeemed',(int)$promo['id'],['user_id'=>$userId,'redemption_id'=>$id,'ledger_id'=>$ledger,'days'=>$promo['duration_days']!==null?(int)$promo['duration_days']:null,'forever'=>$forever,'actor_type'=>'user']);
            $this->pdo->commit();return ['redemption_id'=>$id,'already_activated'=>false,'revoked'=>false,'entitlement'=>(new EntitlementService($this->pdo))->check($userId)->json()];
        } catch(\Throwable $e){if($this->pdo->inTransaction())$this->pdo->rollBack();throw $e;}
    }
    public function revoke(int $actor,int $codeId,bool $grants): void
    {
        $this->owner($actor);if($this->pdo->inTransaction())throw new \LogicException('transaction_already_active');$this->pdo->beginTransaction();
        try {
            $q=$this->pdo->prepare('SELECT id FROM promo_codes WHERE id=? FOR UPDATE');$q->execute([$codeId]);if(!$q->fetchColumn())throw new \DomainException('promo_unavailable');
            $q=$this->pdo->prepare('UPDATE promo_codes SET revoked_at=COALESCE(revoked_at,UTC_TIMESTAMP(6)) WHERE id=?');$q->execute([$codeId]);$changed=$q->rowCount()>0;
            if($grants){$q=$this->pdo->prepare('UPDATE promo_redemptions SET revoked_at=UTC_TIMESTAMP(6) WHERE promo_id=? AND revoked_at IS NULL');$q->execute([$codeId]);$changed=$changed||$q->rowCount()>0;}
            if($changed)$this->audit($actor,$grants?'promo_revoked_with_grants':'promo_revoked',$codeId,['revoke_grants'=>$grants]);
            $this->pdo->commit();
        }catch(\Throwable $e){if($this->pdo->inTransaction())$this->pdo->rollBack();throw $e;}
    }
    public function revokeRedemption(int $actor,int $redemptionId): void
    {
        $this->owner($actor);
        if ($this->pdo->inTransaction()) throw new \LogicException('transaction_already_active');
        if($this->pdo->inTransaction())throw new \LogicException('transaction_already_active');$this->pdo->beginTransaction();
        try {
            // Lock the account first, as redemption does, to serialize its access changes.
            $q=$this->pdo->prepare('SELECT user_id FROM promo_redemptions WHERE id=?');
            $q->execute([$redemptionId]);$userId=$q->fetchColumn();
            if($userId===false)throw new \DomainException('promo_unavailable');
            $q=$this->pdo->prepare('SELECT id FROM users WHERE id=? FOR UPDATE');$q->execute([$userId]);
            $q=$this->pdo->prepare('SELECT promo_id,user_id,ledger_id,revoked_at FROM promo_redemptions WHERE id=? FOR UPDATE');
            $q->execute([$redemptionId]);$row=$q->fetch(PDO::FETCH_ASSOC);
            if(!$row)throw new \DomainException('promo_unavailable');
            if($row['revoked_at']===null){
                $q=$this->pdo->prepare('UPDATE promo_redemptions SET revoked_at=UTC_TIMESTAMP(6) WHERE id=? AND revoked_at IS NULL');
                $q->execute([$redemptionId]);
                $this->audit($actor,'promo_redemption_revoked',(int)$row['promo_id'],[
                    'user_id'=>(int)$row['user_id'],'redemption_id'=>$redemptionId,'ledger_id'=>(int)$row['ledger_id'],
                ]);
            }
            // Keep the one-use record and immutable grant. Revocation never refunds an activation.
            $this->pdo->commit();
        }catch(\Throwable $e){if($this->pdo->inTransaction())$this->pdo->rollBack();throw $e;}
    }
    private function audit(int $actor,string $action,int $id,array $data): void
    {
        $q=$this->pdo->prepare("INSERT INTO audit_log(admin_id,action,entity_type,entity_id,reason,after_json) VALUES (?,?,'promo_code',?,'owner_promo',?)");
        $q->execute([$actor,$action,$id,json_encode($data,JSON_THROW_ON_ERROR)]);
    }
}
