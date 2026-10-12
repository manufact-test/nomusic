<?php
declare(strict_types=1);
namespace Celikom\Support;
final class SupportAdminView
{
 public function __construct(private readonly \PDO $pdo){}
 private static function e(mixed $s):string{return htmlspecialchars((string)$s,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}
 private static function messageBody(string $body):string {
  // Display earlier generated reports as message text without changing stored records.
  if(str_starts_with($body,"Обращение в техподдержку CELIKOM\n\n")) {
   $body=substr($body,strlen("Обращение в техподдержку CELIKOM\n\n"));
   $body=preg_replace('/\n\nВерсия расширения: [^\n]*\nСостояние: [^\n]*\nTrack ID: [^\n]*\nСвязь с вкладкой: [^\n]*$/u','',$body)??$body;
  }
  return $body;
 }
 private static function uuid():string{$b=random_bytes(16);$b[6]=chr((ord($b[6])&15)|64);$b[8]=chr((ord($b[8])&63)|128);$h=bin2hex($b);return substr($h,0,8).'-'.substr($h,8,4).'-'.substr($h,12,4).'-'.substr($h,16,4).'-'.substr($h,20);}
 private static function page(int $page,int $size):int{return (max(1,min(100000,$page))-1)*$size;}
 private static function status(string $status):string{return $status==='open'?'Новое':'Закрыто';}
 public function render(string $csrf,int $selected,int $page=1,int $messagePage=1,int $account=0):string{
  $html='<section class="panel"><h1>Техподдержка</h1>';
  if($selected>0){
   try{$thread=(new SupportService($this->pdo))->thread($selected,null,$messagePage);}catch(\DomainException){return $html.'<p>Обращение не найдено.</p></section>';}
   $q=$this->pdo->prepare('SELECT u.id,u.email FROM users u JOIN support_tickets t ON t.user_id=u.id WHERE t.id=?');$q->execute([$selected]);$user=$q->fetch(\PDO::FETCH_ASSOC);
   $html.='<h2>Обращение №'.$selected.' · '.self::status($thread['status']).'</h2><p>'.self::e($user['email']).'</p>';
   foreach($thread['messages'] as $m){
    $html.='<p style="margin:16px 0 8px">'.($m['author']==='user'?'Сообщение':'Ответ поддержки').'</p><article style="padding:16px;border:1px solid #555;border-radius:12px"><p style="white-space:pre-wrap;overflow-wrap:anywhere">'.self::e(self::messageBody($m['body'])).'</p></article>';
   }
   if($thread['has_more'])$html.='<p><a href="/admin?tab=support&amp;ticket='.$selected.'&amp;message_page='.($messagePage+1).'">Предыдущие сообщения</a></p>';
   if($messagePage>1)$html.='<p><a href="/admin?tab=support&amp;ticket='.$selected.'&amp;message_page='.($messagePage-1).'">Более новые сообщения</a></p>';
   if($thread['status']==='open')$html.='<form method="post" action="/admin/support/reply" style="margin-top:20px"><input type="hidden" name="csrf" value="'.self::e($csrf).'"><input type="hidden" name="ticket" value="'.$selected.'"><input type="hidden" name="request_key" value="'.self::uuid().'"><label>Ответ пользователю<textarea name="message" maxlength="2000" rows="5" required style="display:block;width:100%;box-sizing:border-box;margin:12px 0"></textarea></label><button type="submit">Отправить</button></form>';
   return $html.'<p style="margin:20px 0"><a href="/admin?tab=support&amp;account='.(int)$user['id'].'">Все обращения аккаунта</a></p></section>';
  }
  if($account>0){
   $q=$this->pdo->prepare('SELECT email FROM users WHERE id=?');$q->execute([$account]);$email=$q->fetchColumn();
   if($email===false)return $html.'<p>Аккаунт не найден.</p></section>';
   $html.='<h2>'.self::e($email).'</h2>';
   $offset=self::page($page,10);
   $q=$this->pdo->prepare("SELECT id,status,created_at FROM support_tickets WHERE user_id=? ORDER BY (status='open') DESC,id DESC LIMIT 11 OFFSET $offset");$q->execute([$account]);$rows=$q->fetchAll(\PDO::FETCH_ASSOC);$more=count($rows)>10;
   $html.='<div class="table-wrap"><table><thead><tr><th>Обращение</th><th>Статус</th><th></th></tr></thead><tbody>';
   foreach(array_slice($rows,0,10) as $row)$html.='<tr><td>№'.(int)$row['id'].'</td><td>'.self::status($row['status']).'</td><td><a class="button" href="/admin?tab=support&amp;ticket='.(int)$row['id'].'">Посмотреть</a></td></tr>';
   $html.='</tbody></table></div>'.$this->pagination($page,$more,'&amp;account='.$account);
   return $html.'<p style="margin:20px 0"><a href="/admin?tab=support">Все аккаунты</a></p></section>';
  }
  $offset=self::page($page,20);
  $rows=$this->pdo->query("SELECT u.id,u.email,COUNT(*) AS total,SUM(t.status='open') AS new_count,MAX(t.id) AS latest FROM support_tickets t JOIN users u ON u.id=t.user_id GROUP BY u.id,u.email ORDER BY (SUM(t.status='open')>0) DESC,MAX(t.id) DESC LIMIT 21 OFFSET $offset")->fetchAll(\PDO::FETCH_ASSOC);$more=count($rows)>20;
  $html.='<div class="table-wrap"><table><thead><tr><th>Аккаунт</th><th>Новые</th><th>Всего</th><th></th></tr></thead><tbody>';
  foreach(array_slice($rows,0,20) as $row)$html.='<tr><td>'.self::e($row['email']).'</td><td>'.(int)$row['new_count'].'</td><td>'.(int)$row['total'].'</td><td><a class="button" href="/admin?tab=support&amp;account='.(int)$row['id'].'">Посмотреть</a></td></tr>';
  $html.='</tbody></table></div>';
  if(!$rows)$html.='<p>Обращений пока нет.</p>';
  return $html.$this->pagination($page,$more,'').'</section>';
 }
 private function pagination(int $page,bool $more,string $extra):string{
  $links=[];
  if($page>1)$links[]='<a href="/admin?tab=support'.$extra.'&amp;page='.($page-1).'">Назад</a>';
  if($more)$links[]='<a href="/admin?tab=support'.$extra.'&amp;page='.($page+1).'">Далее</a>';
  return $links?'<p style="margin:20px 0">'.implode(' · ',$links).'</p>':'';
 }
}
