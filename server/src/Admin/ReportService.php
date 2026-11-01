<?php

declare(strict_types=1);

namespace Celikom\Admin;

/** Minimal, owner-test-only report intake until Stage 9 user sessions. */
final class ReportService
{
    public function __construct(private readonly \PDO $pdo, private readonly string $privacyKey) {}

    public function submit(array $data): array
    {
        $id = $data['replacement_id'] ?? null;
        $category = $data['category'] ?? null;
        $details = $data['details'] ?? '';
        $installation = $data['installation_id'] ?? null;
        if (!is_int($id) || $id <= 0
            || !in_array($category, ['wrong_track','bad_quality','broken_audio','rights','other'], true)
            || !is_string($details) || strlen($details) > 500 || !preg_match('//u', $details)
            || preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F]/', $details)
            || !is_string($installation)
            || !preg_match('/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/iD', $installation)
            || strlen($this->privacyKey) < 32) {
            throw new \InvalidArgumentException('invalid_report');
        }
        $reporter = hash_hmac('sha256', strtolower($installation), $this->privacyKey);
        $this->pdo->beginTransaction();
        try {
            $lock = $this->pdo->prepare('SELECT status,is_active FROM track_replacements WHERE id=? FOR UPDATE');
            $lock->execute([$id]);
            $replacement = $lock->fetch(\PDO::FETCH_ASSOC);
            if (!$replacement || $replacement['status'] !== 'approved' || (int)$replacement['is_active'] !== 1) {
                throw new \DomainException('replacement_unavailable');
            }
            $count = $this->pdo->prepare('SELECT COUNT(*) FROM reports
                WHERE reporter_hash=? AND created_at>DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 DAY)');
            $count->execute([$reporter]);
            if ((int)$count->fetchColumn() >= 8) throw new \DomainException('report_rate_limited');
            $existing=$this->pdo->prepare("SELECT id FROM reports WHERE replacement_id=? AND reporter_hash=?
                AND category=? AND status='pending' ORDER BY id DESC LIMIT 1");
            $existing->execute([$id,$reporter,$category]);
            $old=$existing->fetchColumn();
            if ($old !== false) {
                $this->pdo->commit();
                return ['status'=>'pending','report_id'=>(int)$old,'duplicate'=>true];
            }
            $this->pdo->prepare("INSERT INTO reports(replacement_id,reporter_hash,category,details)
                VALUES(?,?,?,?)")->execute([$id,$reporter,$category,trim($details)]);
            $reportId=(int)$this->pdo->lastInsertId();
            $this->pdo->commit();
            return ['status'=>'pending','report_id'=>$reportId,'duplicate'=>false];
        }catch(\Throwable $error){
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }
}
