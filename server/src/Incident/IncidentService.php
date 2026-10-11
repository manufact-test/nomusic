<?php

declare(strict_types=1);

namespace Celikom\Incident;

use PDO;

final class IncidentService
{
    public function __construct(private readonly PDO $pdo) {}

    public static function micros(string $value): int
    {
        $date = new \DateTimeImmutable($value, new \DateTimeZone('UTC'));
        return (int)$date->format('U') * 1000000 + (int)$date->format('u');
    }

    public static function date(int $value): string
    {
        return gmdate('Y-m-d H:i:s', intdiv($value, 1000000)) . sprintf('.%06d', $value % 1000000);
    }

    /** Union first: an entitlement cannot expire while a confirmed outage is running. */
    public static function extendedUntil(string $from, string $until, array $intervals): string
    {
        $start = self::micros($from); $end = self::micros($until);
        usort($intervals, static fn(array $a, array $b): int => strcmp($a[0], $b[0]));
        $union = [];
        foreach ($intervals as [$a, $b]) {
            $left = self::micros($a); $right = self::micros($b);
            if ($right <= $left) continue;
            $last = count($union) - 1;
            if ($last >= 0 && $left <= $union[$last][1]) $union[$last][1] = max($right, $union[$last][1]);
            else $union[] = [$left, $right];
        }
        foreach ($union as [$left, $right]) {
            if ($left >= $end) break;
            if ($right > $start) $end += $right - max($start, $left);
        }
        return self::date($end);
    }

    public function intervals(string $service = 'yandex', bool $closedOnly = false): array
    {
        $q = $this->pdo->prepare('SELECT started_at, COALESCE(ended_at, UTC_TIMESTAMP(6)) AS ended_at
            FROM service_incidents WHERE service=? AND freeze_entitlements=1'
            . ($closedOnly ? ' AND ended_at IS NOT NULL' : '') . ' ORDER BY started_at,id');
        $q->execute([$service]);
        return array_map(static fn(array $r): array => [$r['started_at'], $r['ended_at']], $q->fetchAll(PDO::FETCH_ASSOC));
    }

    public function state(string $service = 'yandex'): array
    {
        $q = $this->pdo->prepare('SELECT COUNT(*) FROM service_incidents WHERE service=? AND ended_at IS NULL');
        $q->execute([$service]);
        return ['active' => (int)$q->fetchColumn() > 0, 'service' => $service,
            'message' => 'Временно недоступна подмена в Яндекс Музыке. Оригинал продолжает работать; время доступа будет компенсировано.'];
    }

    public function validUntil(string $from, string $until, string $service = 'yandex'): string
    {
        return self::extendedUntil($from, $until, $this->intervals($service));
    }

    private function lock(string $service): void
    {
        if (!preg_match('/^[a-z][a-z0-9_]{0,39}$/D', $service)) throw new \InvalidArgumentException('invalid_service');
        $q = $this->pdo->prepare('INSERT IGNORE INTO service_incident_locks(service) VALUES (?)'); $q->execute([$service]);
        $q = $this->pdo->prepare('SELECT service FROM service_incident_locks WHERE service=? FOR UPDATE'); $q->execute([$service]);
        $q->fetchColumn();
    }

    public function start(int $adminId, string $reason, string $key, string $service = 'yandex'): int
    {
        $reason = trim($reason);
        if ($reason === '' || preg_match_all('/./us', $reason) > 500 || !preg_match('//u', $reason) || !preg_match('/^[a-f0-9]{64}$/D', $key))
            throw new \InvalidArgumentException('invalid_incident');
        if ($this->pdo->inTransaction()) throw new \LogicException('incident_transaction_open');
        $this->pdo->beginTransaction();
        try {
            $this->lock($service);
            $q = $this->pdo->prepare('SELECT id,service,reason FROM service_incidents WHERE request_key=? FOR UPDATE'); $q->execute([$key]);
            if ($row = $q->fetch(PDO::FETCH_ASSOC)) {
                if ($row['service'] !== $service || $row['reason'] !== $reason) throw new \DomainException('incident_conflict');
                $this->pdo->commit(); return (int)$row['id'];
            }
            $q = $this->pdo->prepare('INSERT INTO service_incidents(service,request_key,reason,started_at,created_by)
                VALUES (?,?,?,UTC_TIMESTAMP(6),?)'); $q->execute([$service,$key,$reason,$adminId]);
            $id = (int)$this->pdo->lastInsertId(); $this->audit($adminId, 'incident_started', $id, $service);
            $this->pdo->commit(); return $id;
        } catch (\Throwable $e) { if ($this->pdo->inTransaction()) $this->pdo->rollBack(); throw $e; }
    }

    public function resolve(int $adminId, int $id): bool
    {
        if ($this->pdo->inTransaction()) throw new \LogicException('incident_transaction_open');
        // Discover service before the transaction; no stale repeatable-read
        // snapshot may precede the service mutex during concurrent resolutions.
        $q = $this->pdo->prepare('SELECT service FROM service_incidents WHERE id=?'); $q->execute([$id]);
        $service = $q->fetchColumn(); if (!is_string($service)) throw new \DomainException('incident_missing');
        $this->pdo->beginTransaction();
        try {
            $this->lock($service);
            $q = $this->pdo->prepare('SELECT ended_at FROM service_incidents WHERE id=? FOR UPDATE'); $q->execute([$id]);
            $incident = $q->fetch(PDO::FETCH_ASSOC);
            if ($incident['ended_at'] !== null) { $this->pdo->commit(); return false; }
            $q = $this->pdo->prepare('UPDATE service_incidents SET ended_at=UTC_TIMESTAMP(6),resolved_by=? WHERE id=?');
            $q->execute([$adminId,$id]);
            $intervals = $this->intervals($service, true);
            $grants = $this->pdo->query("SELECT id,valid_from,valid_until FROM entitlement_ledger
                WHERE source IN ('trial','subscription') AND valid_from IS NOT NULL AND valid_until IS NOT NULL
                ORDER BY id FOR UPDATE")->fetchAll(PDO::FETCH_ASSOC);
            $sum = $this->pdo->prepare('SELECT COALESCE(SUM(c.microseconds),0) FROM incident_compensations c
                JOIN service_incidents i ON i.id=c.incident_id WHERE c.ledger_id=? AND i.service=?');
            $insert = $this->pdo->prepare('INSERT INTO incident_compensations(incident_id,ledger_id,microseconds) VALUES (?,?,?)');
            foreach ($grants as $grant) {
                $total = self::micros(self::extendedUntil($grant['valid_from'],$grant['valid_until'],$intervals)) - self::micros($grant['valid_until']);
                $sum->execute([$grant['id'],$service]); $delta = $total - (int)$sum->fetchColumn();
                if ($delta > 0) $insert->execute([$id,$grant['id'],$delta]);
            }
            $this->audit($adminId, 'incident_resolved', $id, $service);
            $this->pdo->commit(); return true;
        } catch (\Throwable $e) { if ($this->pdo->inTransaction()) $this->pdo->rollBack(); throw $e; }
    }

    private function audit(int $actor, string $action, int $id, string $service): void
    {
        $q = $this->pdo->prepare('INSERT INTO audit_log(admin_id,action,entity_type,entity_id,reason,after_json)
            VALUES (?,?,?,?,?,?)');
        $q->execute([$actor,$action,'service_incident',$id,'confirmed_service_outage',json_encode(['service'=>$service],JSON_THROW_ON_ERROR)]);
    }
}
