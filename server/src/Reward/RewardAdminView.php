<?php

declare(strict_types=1);

namespace Celikom\Reward;

use PDO;

final class RewardAdminView
{
    public function __construct(private readonly PDO $pdo) {}
    private static function e(mixed $value):string {return htmlspecialchars((string)$value,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}

    public function render(string $csrf,int $page,bool $edit=false,int $account=0,int $songPage=1):string
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
        $count=(int)$this->pdo->query('SELECT COUNT(DISTINCT user_id) FROM reward_ledger')->fetchColumn();
        $pages=max(1,(int)ceil($count/25));$page=min(max(1,$page),$pages);$offset=($page-1)*25;
        $accounts=$this->pdo->query("SELECT l.user_id,u.email,COUNT(*) AS songs,
            SUM(CASE WHEN l.status IN ('approved','used') THEN l.discount_percent ELSE 0 END) AS earned,
            MAX(l.id) AS latest FROM reward_ledger l JOIN users u ON u.id=l.user_id
            GROUP BY l.user_id,u.email ORDER BY latest DESC,l.user_id DESC LIMIT 25 OFFSET $offset")->fetchAll(PDO::FETCH_ASSOC);
        $html.='<section class="panel"><h2>Начисления за песни</h2><p>Аккаунтов: '.$count.' · Страница '.$page.' из '.$pages.'</p>';
        if(!$accounts) $html.='<p>После одобрения новой пользовательской версии здесь появится её бонус.</p>';
        foreach($accounts as $user) {
            $id=(int)$user['user_id'];$base='/admin?tab=rewards&amp;page='.$page.'&amp;account='.$id;
            $html.='<article class="panel reward-account"><h2>Аккаунт #'.$id.' · '.self::e($user['email']).'</h2>'
                .'<p>Учтено песен: '.(int)$user['songs'].' · Начислено: <strong>'.(int)$user['earned'].'%</strong></p>';
            if($account!==$id) $html.='<a class="btn" href="'.$base.'">Песни и бонусы</a>';
            else {
                $html.='<a href="/admin?tab=rewards&amp;page='.$page.'">Свернуть</a>';
                $songPages=max(1,(int)ceil((int)$user['songs']/25));$selectedPage=min(max(1,$songPage),$songPages);$songOffset=($selectedPage-1)*25;
                $q=$this->pdo->prepare("SELECT l.*,t.service_track_id,t.title,t.artist,(l.expires_at<=UTC_TIMESTAMP(6)) AS is_expired FROM reward_ledger l
                    JOIN track_replacements r ON r.id=l.replacement_id JOIN tracks t ON t.id=r.track_id
                    WHERE l.user_id=? ORDER BY l.id DESC LIMIT 25 OFFSET $songOffset");$q->execute([$id]);$rows=$q->fetchAll(PDO::FETCH_ASSOC);
                foreach($rows as $row) $html.=$this->song($row);
                $html.='<nav class="pagination" aria-label="Песни аккаунта"><span>Песни · Страница '.$selectedPage.' из '.$songPages.'</span> ';
                if($selectedPage>1) $html.='<a href="'.$base.'&amp;song_page='.($selectedPage-1).'">Назад</a> ';
                if($selectedPage<$songPages) $html.='<a href="'.$base.'&amp;song_page='.($selectedPage+1).'">Далее</a>';
                $html.='</nav>';
            }
            $html.='</article>';
        }
        $html.='<nav class="pagination" aria-label="Страницы аккаунтов">';
        if($page>1) $html.='<a href="/admin?tab=rewards&amp;page='.($page-1).'">Назад</a> ';
        if($page<$pages) $html.='<a href="/admin?tab=rewards&amp;page='.($page+1).'">Далее</a>';
        return $html.'</nav></section>';
    }

    private function song(array $row):string
    {
        $label=match($row['status']) {'approved'=>(bool)$row['is_expired']?'Срок бонуса истёк':'Бонус начислен','pending'=>'Ранее учтённый вклад без начисления',
            'rejected'=>$row['granted_at']!==null?'Начисление отменено':'Без награды','used'=>'Использован','expired'=>'Срок бонуса истёк',default=>'Неизвестное состояние'};
        $html='<article class="reward-card"><h3>#'.(int)$row['id'].' · '.self::e($label).'</h3><p>'.self::e($row['artist'].' — '.$row['title'])
            .' · Track ID '.self::e($row['service_track_id']).'</p>';
        if($row['grant_mode']==='automatic') {
            $q=$this->pdo->prepare('SELECT available_from,discount_percent,validity_days FROM reward_allocations WHERE reward_id=? ORDER BY part_index');$q->execute([$row['id']]);
            $html.='<p>Начислено автоматически: <strong>'.(int)$row['discount_percent'].'%</strong></p>';
            foreach($q->fetchAll(PDO::FETCH_ASSOC) as $part) $html.='<p>'.self::e(substr($part['available_from'],0,7)).': '.(int)$part['discount_percent'].'% · '
                .(int)$part['validity_days'].' дней после оплаты</p>';
        } elseif($row['granted_at']!==null) $html.='<p>Ранее начисленный бонус: '.(int)$row['discount_percent'].'% · до '.self::e($row['expires_at']).' UTC</p>';
        return $html.'</article>';
    }
}
