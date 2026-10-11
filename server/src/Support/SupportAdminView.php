<?php
declare(strict_types=1);
namespace Celikom\Support;
final class SupportAdminView
{
 public function __construct(private readonly \PDO $pdo){}
 private static function e(mixed $s):string{return htmlspecialchars((string)$s,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}
 private static function uuid():string{$b=random_bytes(16);$b[6]=chr((ord($b[6])&15)|64);$b[8]=chr((ord($b[8])&63)|128);$h=bin2hex($b);return substr($h,0,8).'-'.substr($h,8,4).'-'.substr($h,12,4).'-'.substr($h,16,4).'-'.substr($h,20);}
 public function render(string $csrf,int $selected,int $page=1):string{
  $html='<section class="panel"><h1>Техподдержка</h1><p>Обращения пользователей и ответы. Ответ сохраняется здесь и отправляется на подтверждённую почту пользователя.</p>';
  if($selected>0){
   try{$thread=(new SupportService($this->pdo))->thread($selected);}catch(\DomainException){return $html.'<p>Обращение не найдено.</p></section>';}
   $q=$this->pdo->prepare('SELECT u.email FROM users u JOIN support_tickets t ON t.user_id=u.id WHERE t.id=?');$q->execute([$selected]);
   $html.='<h2>Обращение №'.$selected.'</h2><p>'.self::e($q->fetchColumn()).'</p>';
   foreach($thread['messages'] as $m){$html.='<article style="margin:16px 0;padding:16px;border:1px solid #555;border-radius:12px"><strong>'.($m['author']==='user'?'Пользователь':'Поддержка').'</strong><p style="white-space:pre-wrap;overflow-wrap:anywhere">'.self::e($m['body']).'</p></article>';}
   $q=$this->pdo->prepare('SELECT delivery FROM support_messages WHERE ticket_id=? ORDER BY id DESC LIMIT 1');$q->execute([$selected]);$state=$q->fetchColumn();
   $html.='<p>Отправка письма: '.self::e(match($state){'sent'=>'почтовый сервер принял письмо','pending'=>'ожидает отправки','sending'=>'результат пока не подтверждён',default=>'не подтверждена; ответ доступен в CELIKOM'}).'</p>';
   $html.='<form method="post" action="/admin/support/reply"><input type="hidden" name="csrf" value="'.self::e($csrf).'"><input type="hidden" name="ticket" value="'.$selected.'"><input type="hidden" name="request_key" value="'.self::uuid().'"><label>Ответ пользователю<textarea name="message" maxlength="2000" rows="5" required style="display:block;width:100%;box-sizing:border-box;margin:12px 0"></textarea></label><button type="submit">Сохранить и отправить ответ</button></form>';
   $html.='<form method="post" action="/admin/support/close" style="margin-top:16px"><input type="hidden" name="csrf" value="'.self::e($csrf).'"><input type="hidden" name="ticket" value="'.$selected.'"><button type="submit">Закрыть обращение</button></form><p><a href="/admin?tab=support">Все обращения</a></p>';
  }
  $offset=(max(1,min(100000,$page))-1)*20;
  $rows=$this->pdo->query("SELECT t.id,t.status,t.created_at,u.email FROM support_tickets t JOIN users u ON u.id=t.user_id ORDER BY t.id DESC LIMIT 20 OFFSET $offset")->fetchAll(\PDO::FETCH_ASSOC);
  $html.='<div class="table-wrap"><table><thead><tr><th>Обращение</th><th>Аккаунт</th><th>Статус</th></tr></thead><tbody>';
  foreach($rows as $row)$html.='<tr><td><a href="/admin?tab=support&amp;ticket='.(int)$row['id'].'">№'.(int)$row['id'].'</a></td><td>'.self::e($row['email']).'</td><td>'.self::e(match($row['status']){'open'=>'Новое','answered'=>'Есть ответ',default=>'Закрыто'}).'</td></tr>';
  $html.='</tbody></table></div><p>';
  if($page>1)$html.='<a href="/admin?tab=support&amp;page='.($page-1).'">Назад</a> · ';
  if(count($rows)===20)$html.='<a href="/admin?tab=support&amp;page='.($page+1).'">Далее</a>';
  return $html.'</p></section>';
 }
}
