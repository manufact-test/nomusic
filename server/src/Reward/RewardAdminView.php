<?php

declare(strict_types=1);

namespace Celikom\Reward;

use PDO;

final class RewardAdminView
{
    public function __construct(private readonly PDO $pdo) {}
    private static function e(mixed $value):string {return htmlspecialchars((string)$value,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}

    public function render(string $csrf,int $page,bool $edit=false):string
    {
        $policy=(new RewardPolicyService($this->pdo))->read();$csrf=self::e($csrf);
        $editing=$edit || !$policy['enabled'];
        $html='<section class="panel"><h1>Награды за вклад</h1><p>Одобрите песню — автор автоматически получит бонус. '
            .'Проценты сверх месячного предела сохраняются для следующих месяцев.</p><h2>Настройки</h2>';
        if($editing) $html.='<form class="reward-policy-form" method="post" action="/admin/rewards/policy"><input type="hidden" name="csrf" value="'.$csrf.'">'
            .'<input type="hidden" name="version" value="'.$policy['version'].'">';
        foreach(['upload_discount_percent'=>['Бонус за одну одобренную песню, %',100],
            'max_discount_percent'=>['Максимальная скидка за месяц, %',100],
            'validity_days'=>['Срок действия скидки после оплаты, дней',3660]] as $key=>[$label,$max]) {
            if($editing) $html.='<label class="form-field">'.self::e($label).'<input type="number" name="'.$key.'" min="1" max="'.$max.'" step="1" required value="'.$policy[$key].'"></label>';
            else $html.='<p>'.self::e($label).': <strong>'.$policy[$key].'</strong></p>';
        }
        if($editing) $html.='<button class="btn" type="submit">Сохранить</button></form>';
        else $html.='<a class="btn" href="/admin?tab=rewards&amp;edit=1">Изменить</a>';
        $html.='<p><small>Предел считается за календарный месяц UTC. Перенесённые бонусы ждут своей очереди и не сгорают до оплаты. '
            .'Сохранённые настройки действуют для новых одобрений. Платежи пока не подключены.</small></p></section>';
        $count=(int)$this->pdo->query('SELECT COUNT(*) FROM reward_ledger')->fetchColumn();$pages=max(1,(int)ceil($count/25));$page=min(max(1,$page),$pages);
        $offset=($page-1)*25;
        $rows=$this->pdo->query("SELECT l.*,u.email,t.service_track_id,t.title,t.artist FROM reward_ledger l
            JOIN users u ON u.id=l.user_id JOIN track_replacements r ON r.id=l.replacement_id JOIN tracks t ON t.id=r.track_id
            ORDER BY l.id DESC LIMIT 25 OFFSET $offset")->fetchAll(PDO::FETCH_ASSOC);
        $html.='<section class="panel"><h2>Начисления за песни</h2><p>Всего: '.$count.' · Страница '.$page.' из '.$pages.'</p>';
        if(!$rows) $html.='<p>После одобрения новой пользовательской версии здесь появится её бонус.</p>';
        foreach($rows as $row) {
            $label=match($row['status']) {'approved'=>'Бонус начислен','pending'=>'Ранее учтённый вклад без начисления',
                'rejected'=>$row['granted_at']!==null?'Начисление отменено':'Без награды','used'=>'Использован','expired'=>'Срок бонуса истёк',default=>'Неизвестное состояние'};
            $html.='<article class="panel reward-card"><h2>#'.(int)$row['id'].' · '.self::e($label).'</h2><p>'.self::e($row['artist'].' — '.$row['title'])
                .' · Track ID '.self::e($row['service_track_id']).'</p><p>Аккаунт #'.(int)$row['user_id'].' · '.self::e($row['email']).'</p>';
            if($row['grant_mode']==='automatic') {
                $q=$this->pdo->prepare('SELECT available_from,discount_percent,validity_days FROM reward_allocations WHERE reward_id=? ORDER BY part_index');$q->execute([$row['id']]);
                $html.='<p>Начислено автоматически: <strong>'.(int)$row['discount_percent'].'%</strong></p>';
                foreach($q->fetchAll(PDO::FETCH_ASSOC) as $part) $html.='<p>'.self::e(substr($part['available_from'],0,7)).': '.(int)$part['discount_percent'].'% · '
                    .(int)$part['validity_days'].' дней после оплаты</p>';
            } elseif($row['granted_at']!==null) $html.='<p>Ранее начисленный бонус: '.(int)$row['discount_percent'].'% · до '.self::e($row['expires_at']).' UTC</p>';
            $html.='</article>';
        }
        $html.='<nav class="pagination" aria-label="Страницы наград">';
        if($page>1) $html.='<a href="/admin?tab=rewards&amp;page='.($page-1).'">Назад</a> ';
        if($page<$pages) $html.='<a href="/admin?tab=rewards&amp;page='.($page+1).'">Далее</a>';
        return $html.'</nav></section>';
    }
}
