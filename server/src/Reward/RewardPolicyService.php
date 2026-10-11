<?php

declare(strict_types=1);

namespace Celikom\Reward;

use PDO;

/** Owner-only, explicitly configured financial policy. Defaults to disabled. */
final class RewardPolicyService
{
    public function __construct(private readonly PDO $pdo) {}

    public function read(): array
    {
        $row=$this->pdo->query('SELECT * FROM reward_policy WHERE id=1')->fetch(PDO::FETCH_ASSOC);
        if (!$row) throw new \DomainException('reward_policy_missing');
        return array_map(static fn($value):int=>(int)$value,$row);
    }

    public function configure(int $adminId, int $expectedVersion, array $values, string $reason): void
    {
        $bounds=['enabled'=>1,'upload_discount_percent'=>100,'max_discount_percent'=>100,
            'max_reward_per_month'=>10000,'validity_days'=>3660];
        foreach($bounds as $key=>$max) {
            if (!isset($values[$key]) || !is_int($values[$key]) || $values[$key]<0 || $values[$key]>$max)
                throw new \InvalidArgumentException('invalid_reward_policy');
        }
        if ($values['enabled'] && (!$values['upload_discount_percent'] || !$values['max_reward_per_month']
            || !$values['validity_days'] || $values['upload_discount_percent']>$values['max_discount_percent']))
            throw new \InvalidArgumentException('invalid_reward_policy');
        if ($expectedVersion<1 || trim($reason)==='' || mb_strlen($reason)>500)
            throw new \InvalidArgumentException('invalid_reward_policy');
        $this->pdo->beginTransaction();
        try {
            self::owner($this->pdo,$adminId);
            $before=$this->pdo->query('SELECT * FROM reward_policy WHERE id=1 FOR UPDATE')->fetch(PDO::FETCH_ASSOC);
            if (!$before || (int)$before['version']!==$expectedVersion) throw new \DomainException('stale_reward_policy');
            $this->pdo->prepare('UPDATE reward_policy SET enabled=?,upload_discount_percent=?,max_discount_percent=?,
                max_reward_per_month=?,validity_days=?,version=version+1 WHERE id=1')
                ->execute(array_map(static fn($key)=>$values[$key],array_keys($bounds)));
            self::audit($this->pdo,$adminId,'reward_policy_changed','reward_policy',1,$reason,$before,$this->read());
            $this->pdo->commit();
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();throw $error;
        }
    }

    public static function owner(PDO $pdo,int $adminId):void
    {
        $q=$pdo->prepare("SELECT id FROM admins WHERE id=? AND role='owner' AND enabled=1");$q->execute([$adminId]);
        if (!$q->fetchColumn()) throw new \DomainException('reward_owner_required');
    }

    public static function audit(PDO $pdo,int $adminId,string $action,string $type,int $id,string $reason,array $before,array $after):void
    {
        $pdo->prepare('INSERT INTO audit_log(admin_id,action,entity_type,entity_id,reason,before_json,after_json) VALUES(?,?,?,?,?,?,?)')
            ->execute([$adminId,$action,$type,$id,$reason,json_encode($before,JSON_THROW_ON_ERROR),json_encode($after,JSON_THROW_ON_ERROR)]);
    }
}
