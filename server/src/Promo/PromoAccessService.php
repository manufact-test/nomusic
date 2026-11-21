<?php

declare(strict_types=1);

namespace Celikom\Promo;

use PDO;
use Celikom\Incident\IncidentService;

/** Immutable base windows; queued promo windows follow the effective parent deadline. */
final class PromoAccessService
{
    public function __construct(private readonly PDO $pdo, private readonly bool $billingEnabled = false) {}

    public function windows(int $userId, ?array $intervals = null): array
    {
        $intervals ??= (new IncidentService($this->pdo))->intervals();
        $now = (string)$this->pdo->query('SELECT UTC_TIMESTAMP(6)')->fetchColumn();
        $windows = [];
        $q = $this->pdo->prepare("SELECT l.id,l.valid_from,l.valid_until,l.source FROM account_trials t
            JOIN entitlement_ledger l ON l.id=t.ledger_id AND l.user_id=t.user_id
            AND l.source='trial' AND l.reason='first_activation' AND l.valid_from=t.valid_from AND l.valid_until=t.valid_until
            WHERE t.user_id=?"); $q->execute([$userId]);
        $roots = $q->fetchAll(PDO::FETCH_ASSOC);
        if ($this->billingEnabled) {
            $q = $this->pdo->prepare("SELECT l.id,l.valid_from,l.valid_until,l.source FROM billing_payments p
                JOIN subscriptions s ON s.id=p.subscription_id JOIN entitlement_ledger l ON l.id=p.ledger_id
                AND l.user_id=s.user_id AND l.source='subscription' AND l.reason='payment_confirmed'
                AND l.valid_from=p.valid_from AND l.valid_until=p.valid_until
                WHERE s.user_id=? AND p.revoked_at IS NULL"); $q->execute([$userId]);
            $roots = array_merge($roots,$q->fetchAll(PDO::FETCH_ASSOC));
        }
        foreach ($roots as $r) {
            $end = IncidentService::extendedUntil($r['valid_from'],$r['valid_until'],$intervals);
            $windows[(int)$r['id']] = ['from'=>$r['valid_from'],'until'=>$end,'connected'=>$r['valid_from']<=$now && $end>$now,'source'=>$r['source'],'revoked'=>false];
        }
        $q = $this->pdo->prepare("SELECT r.*,l.source,l.reason,l.valid_from AS ledger_from,l.valid_until AS ledger_until
            FROM promo_redemptions r JOIN entitlement_ledger l ON l.id=r.ledger_id AND l.user_id=r.user_id
            WHERE r.user_id=? ORDER BY r.ledger_id"); $q->execute([$userId]);
        foreach ($q->fetchAll(PDO::FETCH_ASSOC) as $r) {
            if ($r['source']!=='promo' || $r['reason']!=='owner_promo_free'
                || $r['ledger_from']!==$r['valid_from'] || $r['ledger_until']!==$r['valid_until']
                || ((int)$r['forever']===1 ? ($r['valid_until']!==null || $r['duration_days']!==null) : ($r['valid_until']===null || IncidentService::micros($r['valid_until'])-IncidentService::micros($r['valid_from']) !== (int)$r['duration_days']*86400000000))) continue;
            $parent = $windows[(int)($r['parent_ledger_id'] ?? 0)] ?? null;
            if($r['parent_ledger_id']!==null && $parent===null)continue;
            $from = max($r['activated_at'],$parent['until'] ?? $r['activated_at']);
            if ($r['revoked_at']!==null) {
                // Remove only this bonus. A later independently issued code retains its own days.
                $windows[(int)$r['ledger_id']] = ['from'=>$r['activated_at'],'until'=>$parent['until'] ?? $r['activated_at'],
                    'connected'=>$parent['connected'] ?? false,'source'=>'promo','revoked'=>true]; continue;
            }
            if ((int)$r['forever']===1) {
                $windows[(int)$r['ledger_id']]=['from'=>$r['activated_at'],'until'=>null,'connected'=>$r['activated_at']<=$now,'source'=>'promo','revoked'=>false]; continue;
            }
            $until = IncidentService::date(IncidentService::micros($from)+(int)$r['duration_days']*86400000000);
            $end = IncidentService::extendedUntil($from,$until,$intervals);
            $connected = ($from<=$now && $end>$now) || ($parent!==null && $parent['connected'] && $from<=$parent['until'] && $end>$now);
            $windows[(int)$r['ledger_id']] = ['from'=>$from,'until'=>$end,'connected'=>$connected,'source'=>'promo','revoked'=>false];
        }
        return $windows;
    }

    public function best(int $userId): ?array
    {
        $best = null;
        foreach ($this->windows($userId) as $id=>$r) {
            if (!$r['revoked'] && $r['connected'] && ($best===null || ($best['until']!==null && ($r['until']===null || $r['until']>$best['until'])))) $best=$r+['ledger_id'=>$id];
        }
        return $best;
    }
}
