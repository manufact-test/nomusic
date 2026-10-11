<?php

declare(strict_types=1);
namespace Celikom\Promo;
use PDO;

final class PromoAdminView
{
    public function __construct(private readonly PDO $pdo) {}
    private static function e(mixed $v): string {return htmlspecialchars((string)$v,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}
    public static function confirmation(array $form): string
    {
        $html='<section class="panel"><h1>Точно хотите выдать доступ навсегда?</h1><p>Бессрочный доступ не закончится автоматически. Вы сможете отозвать отдельную активацию.</p><p>Код: <strong>'.self::e($form['code']??'').'</strong>. Лимит активаций: '.self::e($form['max_activations']??'').'.</p><form method="post" action="/admin/promos/create">';
        foreach(['csrf','code','title','discount_percent','duration_days','forever','max_activations','activation_window','activation_deadline','request_key'] as $key){
            if(is_string($form[$key]??null))$html.='<input type="hidden" name="'.$key.'" value="'.self::e($form[$key]).'">';
        }
        return $html.'<input type="hidden" name="confirm_forever" value="1"><button type="submit">Да, создать бессрочный промокод</button> <a href="/admin?tab=promos&amp;create=1">Отмена</a></form></section>';
    }
    public function render(string $csrf,int $page=1,bool $create=false,bool $activations=false): string
    {
        $hidden='<input type="hidden" name="csrf" value="'.self::e($csrf).'">';
        $html='<section class="panel"><h1>Промокоды</h1><p><a class="btn" href="/admin?tab=promos&amp;create=1">Создать промокод</a> <a href="/admin?tab=promos">Все промокоды</a> <a href="/admin?tab=promos&amp;activations=1">Активации</a></p>';
        if($create){
            $html.='<form class="reward-policy-form" method="post" action="/admin/promos/create">'.$hidden.'<input type="hidden" name="request_key" value="'.bin2hex(random_bytes(32)).'">'
                .'<label class="form-field">Название<input name="title" maxlength="120" required></label><label class="form-field">Текст кода<input name="code" minlength="8" maxlength="64" pattern="[A-Za-z0-9_-]{8,64}" autocomplete="off" required></label><p>От 8 до 64 латинских букв, цифр, дефисов или подчёркиваний. Регистр не имеет значения.</p>'
                .'<label class="form-field">Скидка, %<input type="number" name="discount_percent" min="1" max="100" value="100" required></label><label class="form-field">Срок, дней<input type="number" name="duration_days" min="1" max="3660"></label><label class="form-field"><input type="checkbox" name="forever" value="1"> Навсегда — только для 100% бесплатного доступа</label>'
                .'<label class="form-field">Лимит активаций<input type="number" name="max_activations" min="1" max="1000000" value="1" required></label><label class="form-field">Когда можно активировать<select name="activation_window" required><option value="">Выберите</option><option value="unlimited">Без ограничения даты</option><option value="fixed">До указанной даты</option></select></label><label class="form-field">Последний срок активации, UTC<input type="datetime-local" name="activation_deadline"></label>'
                .'<p>100% выдаёт бесплатный доступ. Дни добавляются к остатку. Один аккаунт использует конкретный код один раз. Скидки меньше 100% начнут применяться после подключения оплаты.</p><button type="submit">Создать промокод</button></form>';
        }
        $page=max(1,min($page,1000000));$offset=($page-1)*25;
        if($activations){
            $q=$this->pdo->query("SELECT r.*,p.code,p.title,u.email FROM promo_redemptions r JOIN promo_codes p ON p.id=r.promo_id JOIN users u ON u.id=r.user_id ORDER BY r.id DESC LIMIT 26 OFFSET $offset");
            $rows=$q->fetchAll(PDO::FETCH_ASSOC);$more=count($rows)>25;$rows=array_slice($rows,0,25);
            $html.='<h2>Активации</h2><div class="table-shell"><table><thead><tr><th>Аккаунт</th><th>Промокод</th><th>Активирован, UTC</th><th>Доступ</th><th>Действие</th></tr></thead><tbody>';
            $windows=[];
            foreach($rows as $row){
                $user=(int)$row['user_id'];$windows[$user]??=(new PromoAccessService($this->pdo))->windows($user);
                $window=$windows[$user][(int)$row['ledger_id']]??null;
                $duration=(int)$row['forever']===1?'Навсегда':(int)$row['duration_days'].' дней';
                $status=$row['revoked_at']!==null?'Отозван':($window===null?'Недоступен':($window['until']===null?'Навсегда':'До '.$window['until'].' UTC'));
                $html.='<tr><td>'.self::e($row['email']).' · #'.$user.'</td><td>'.self::e($row['code']).'<br>'.self::e($row['title']).'</td><td>'.self::e($row['activated_at']).'</td><td>'.self::e($duration).'<br>'.self::e($status).'</td><td>';
                if($row['revoked_at']===null)$html.='<form method="post" action="/admin/promos/revoke-activation">'.$hidden.'<input type="hidden" name="id" value="'.(int)$row['id'].'"><button type="submit">Отозвать</button></form>';
                $html.='</td></tr>';
            }
            $html.='</tbody></table></div><p>Отзыв убирает только доступ этой активации. Другие источники доступа сохраняются; повторная активация того же кода запрещена.</p>';
        }else{
            $rows=$this->pdo->query("SELECT * FROM promo_codes ORDER BY id DESC LIMIT 26 OFFSET $offset")->fetchAll(PDO::FETCH_ASSOC);$more=count($rows)>25;$rows=array_slice($rows,0,25);
            $html.='<div class="table-shell"><table><thead><tr><th>Код</th><th>Скидка и срок</th><th>Активации</th><th>Последний срок, UTC</th><th>Действие</th></tr></thead><tbody>';
            foreach($rows as $row){
                $html.='<tr><td>'.self::e($row['code']).'<br>'.self::e($row['title']).'</td><td>'.(int)$row['discount_percent'].'% · '.((int)$row['forever']===1?'Навсегда':(int)$row['duration_days'].' дней').'</td><td>'.(int)$row['used_activations'].' / '.(int)$row['max_activations'].'</td><td>'.self::e($row['activation_deadline']??'Без ограничения').'</td><td>';
                if($row['revoked_at']===null)$html.='<form method="post" action="/admin/promos/revoke">'.$hidden.'<input type="hidden" name="id" value="'.(int)$row['id'].'"><button type="submit">Закрыть активации</button></form>';
                else $html.='Новые активации закрыты';
                $html.='</td></tr>';
            }
            $html.='</tbody></table></div><p>Закрытие кода запрещает новые активации. Для отзыва выданного доступа откройте «Активации».</p>';
        }
        $base='/admin?tab=promos'.($activations?'&amp;activations=1':'');
        if($page>1)$html.='<a href="'.$base.'&amp;page='.($page-1).'">Назад</a> ';
        if($more)$html.='<a href="'.$base.'&amp;page='.($page+1).'">Далее</a>';
        return $html.'</section>';
    }
}
