<?php

declare(strict_types=1);

namespace Celikom\Reward;

use PDO;

/** Owner-only controls using the existing server-rendered administration shell. */
final class RewardAdminView
{
    public function __construct(private readonly PDO $pdo) {}
    private static function e(mixed $value):string {return htmlspecialchars((string)$value,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}

    public function render(string $csrf,int $page):string
    {
        $policy=(new RewardPolicyService($this->pdo))->read();$csrf=self::e($csrf);
        $html='<section class="panel"><h1>Награды за вклад</h1><p>Награда рассматривается после одобрения версии песни. '
            .'Сейчас можно учитывать и начислять скидочные бонусы. Применение к оплате будет доступно после подключения платежей. '
            .'Бонус не продлевает пробный период и не открывает доступ.</p><h2>Правила начисления</h2>'
            .'<form class="reward-policy-form" method="post" action="/admin/rewards/policy"><input type="hidden" name="csrf" value="'.$csrf.'">'
            .'<input type="hidden" name="version" value="'.$policy['version'].'">';
        foreach(['upload_discount_percent'=>['Скидочный бонус за одну одобренную загрузку, %',100],
            'max_discount_percent'=>['Максимальная суммарная скидка от этих бонусов, %',100],
            'max_reward_per_month'=>['Максимум начислений одному аккаунту за календарный месяц (UTC)',10000],
            'validity_days'=>['Срок действия начисленного бонуса, дней',3660]] as $key=>[$label,$max]) {
            $html.='<label class="form-field">'.self::e($label).'<input type="number" name="'.$key.'" min="0" max="'.$max.'" step="1" required value="'.$policy[$key].'"></label>';
        }
        $html.='<label class="reward-enable"><input type="checkbox" name="enabled" value="1"'.($policy['enabled']?' checked':'').'> Разрешить ручное начисление</label>'
            .'<label class="form-field">Причина изменения<input name="reason" maxlength="500" required></label><button class="btn" type="submit">Сохранить правила</button>'
            .'</form><p><small>Изменение правил не пересчитывает уже начисленный процент и срок. '
            .'Общий предел ограничивает возможную суммарную скидку. Отключение запрещает новые начисления; '
            .'отменённые и истёкшие начисления продолжают учитываться в лимите месяца.</small></p></section>';
        $count=(int)$this->pdo->query('SELECT COUNT(*) FROM reward_ledger')->fetchColumn();$pages=max(1,(int)ceil($count/25));$page=min(max(1,$page),$pages);
        $offset=($page-1)*25;
        $rows=$this->pdo->query("SELECT l.*,u.email,t.service_track_id,t.title,t.artist,
            (l.expires_at<=UTC_TIMESTAMP(6)) AS is_expired
            FROM reward_ledger l JOIN users u ON u.id=l.user_id
            JOIN track_replacements r ON r.id=l.replacement_id JOIN tracks t ON t.id=r.track_id
            ORDER BY l.id DESC LIMIT 25 OFFSET $offset")->fetchAll(PDO::FETCH_ASSOC);
        $html.='<section class="panel"><h2>Вклады и решения</h2><p>Всего: '.$count.' · Страница '.$page.' из '.$pages.'</p>';
        if (!$rows) $html.='<p>Одобренных вкладов для рассмотрения пока нет.</p>';
        foreach($rows as $row) {
            $label=match($row['status']){'pending'=>'Ожидает решения по награде','approved'=>(bool)$row['is_expired']?'Срок бонуса истёк':'Бонус начислен',
                'rejected'=>$row['granted_at']!==null?'Начисление отменено':'Без награды','used'=>'Использован','expired'=>'Срок бонуса истёк',default=>'Неизвестное состояние'};
            $html.='<article class="panel reward-card"><h2>#'.(int)$row['id'].' · '.self::e($label).'</h2><p>'.self::e($row['artist'].' — '.$row['title'])
                .' · Track ID '.self::e($row['service_track_id']).'</p><p>Аккаунт #'.(int)$row['user_id'].' · '.self::e($row['email']).'</p>';
            if($row['granted_at']!==null) $html.='<p>Бонус: '.(int)$row['discount_percent'].'% · действует до '.self::e($row['expires_at']).' UTC</p>';
            $actions=$row['status']==='pending' ? ($policy['enabled']?['approve'=>'Начислить '.$policy['upload_discount_percent'].'%','reject'=>'Не начислять']:['reject'=>'Не начислять'])
                : ($row['status']==='approved' ? ((bool)$row['is_expired']?['expire'=>'Зафиксировать истечение']:['revoke'=>'Отменить начисление']):[]);
            if($actions) {
                $html.='<form class="reward-decision-form" method="post" action="/admin/rewards/action"><input type="hidden" name="csrf" value="'.$csrf.'">'
                    .'<input type="hidden" name="id" value="'.(int)$row['id'].'"><input type="hidden" name="version" value="'.(int)$row['version'].'">'
                    .'<input type="hidden" name="policy_version" value="'.$policy['version'].'"><label class="form-field">Причина решения<input name="reason" maxlength="500" required></label>';
                foreach($actions as $action=>$title) $html.='<button class="btn" name="action" value="'.$action.'" type="submit">'.self::e($title).'</button> ';
                $html.='</form>';
            }
            $html.='</article>';
        }
        $html.='<nav class="pagination" aria-label="Страницы наград">';
        if($page>1) $html.='<a href="/admin?tab=rewards&amp;page='.($page-1).'">Назад</a> ';
        if($page<$pages) $html.='<a href="/admin?tab=rewards&amp;page='.($page+1).'">Далее</a>';
        return $html.'</nav></section>';
    }
}
