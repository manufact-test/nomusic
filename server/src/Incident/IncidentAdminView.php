<?php

declare(strict_types=1);

namespace Celikom\Incident;

use PDO;

final class IncidentAdminView
{
    public function __construct(private readonly PDO $pdo) {}
    private static function e(string $s): string { return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
    public function render(string $csrf): string
    {
        $token = '<input type="hidden" name="csrf" value="'.self::e($csrf).'">';
        $html = '<section class="panel"><h1>Сбои интеграции</h1><p>Объявляйте только подтверждённый общий сбой подмены в Яндекс Музыке. Оригинал остаётся доступным. Потерянное время пробного или оплаченного доступа компенсируется; пересечения не удваивают срок.</p>'
            .'<form method="post" action="/admin/incidents/start">'.$token
            .'<input type="hidden" name="request_key" value="'.bin2hex(random_bytes(32)).'">'
            .'<label>Причина сбоя<input name="reason" required maxlength="500"></label><button type="submit" class="primary">Объявить сбой</button></form></section>';
        $rows = $this->pdo->query("SELECT i.*, (SELECT COUNT(*) FROM incident_compensations c WHERE c.incident_id=i.id) AS grants,
            (SELECT COALESCE(SUM(microseconds),0) FROM incident_compensations c WHERE c.incident_id=i.id) AS compensated
            FROM service_incidents i WHERE service='yandex' ORDER BY (ended_at IS NULL) DESC,id DESC LIMIT 100")->fetchAll(PDO::FETCH_ASSOC);
        if (!$rows) return $html.'<section class="panel"><p>Объявленных сбоев пока нет.</p></section>';
        foreach ($rows as $r) {
            $html.='<section class="panel"><h2>Сбой №'.(int)$r['id'].' · '.($r['ended_at']===null?'Идёт':'Завершён').'</h2><p>'.self::e($r['reason']).'</p><p>Начало UTC: '.self::e($r['started_at']).'</p>';
            if ($r['ended_at']===null) $html.='<form method="post" action="/admin/incidents/resolve">'.$token.'<input type="hidden" name="id" value="'.(int)$r['id'].'"><button type="submit" class="primary">Завершить и компенсировать время</button></form>';
            else $html.='<p>Окончание UTC: '.self::e($r['ended_at']).'</p><p>Учтено сроков доступа: '.(int)$r['grants'].'. Суммарная компенсация: '.self::e(number_format((int)$r['compensated']/1000000,6,'.',' ')).' сек.</p>';
            $html.='</section>';
        }
        return $html;
    }
}
