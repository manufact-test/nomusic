<?php
declare(strict_types=1);
namespace Celikom\Support;
use Celikom\Auth\SmtpMailer;
final class SupportService
{
 public function __construct(private readonly \PDO $pdo, private readonly array $config=[]) {}
 private function validate(string $text,string $key):string {
  $text=trim($text);
  if(strlen($text)<3||strlen($text)>6000||!preg_match('//u',$text)||preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F]/',$text)||!preg_match('/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/D',$key))throw new \InvalidArgumentException('invalid_request');
  return $text;
 }
 public function create(int $user,string $body,string $key):int {
  $body=$this->validate($body,$key);$this->pdo->beginTransaction();
  try {
   // Per-account lock makes rate limits and duplicate handling atomic.
   $q=$this->pdo->prepare("SELECT id FROM users WHERE id=? AND status='active' FOR UPDATE");$q->execute([$user]);if(!$q->fetchColumn())throw new \DomainException('invalid_session');
   $q=$this->pdo->prepare('SELECT id FROM support_tickets WHERE user_id=? AND request_key=?');$q->execute([$user,$key]);$id=$q->fetchColumn();
   if($id){$q=$this->pdo->prepare('SELECT body FROM support_messages WHERE ticket_id=? AND admin_id IS NULL ORDER BY id LIMIT 1');$q->execute([$id]);if($q->fetchColumn()!==$body)throw new \InvalidArgumentException('invalid_request');$this->pdo->commit();return (int)$id;}
   $q=$this->pdo->prepare('SELECT COUNT(*) FROM support_tickets WHERE user_id=? AND created_at>UTC_TIMESTAMP()-INTERVAL 1 HOUR');$q->execute([$user]);if((int)$q->fetchColumn()>=5)throw new \DomainException('rate_limited');
   $this->pdo->prepare('INSERT INTO support_tickets(user_id,request_key) VALUES (?,?)')->execute([$user,$key]);$id=(int)$this->pdo->lastInsertId();
   $this->pdo->prepare('INSERT INTO support_messages(ticket_id,request_key,body) VALUES (?,?,?)')->execute([$id,$key,$body]);$message=(int)$this->pdo->lastInsertId();$this->pdo->commit();
  }catch(\Throwable $e){if($this->pdo->inTransaction())$this->pdo->rollBack();throw $e;}
  $this->deliver($message);return $id;
 }
 public function listForUser(int $user,int $page=1):array {
  $offset=(max(1,min(100000,$page))-1)*5;
  $q=$this->pdo->prepare("SELECT id,status,created_at,updated_at FROM support_tickets WHERE user_id=? ORDER BY id DESC LIMIT 6 OFFSET $offset");$q->execute([$user]);return $q->fetchAll(\PDO::FETCH_ASSOC);
 }
 public function thread(int $id,?int $user=null,int $page=1):array {
  $page=max(1,min(100000,$page));$offset=($page-1)*5;
  $q=$this->pdo->prepare('SELECT id,status,created_at FROM support_tickets WHERE id=?'.($user!==null?' AND user_id=?':''));$q->execute($user!==null?[$id,$user]:[$id]);$ticket=$q->fetch(\PDO::FETCH_ASSOC);if(!$ticket)throw new \DomainException('not_found');
  $q=$this->pdo->prepare("SELECT id,body,created_at,IF(admin_id IS NULL,'user','support') AS author FROM support_messages WHERE ticket_id=? ORDER BY id DESC LIMIT 6 OFFSET $offset");$q->execute([$id]);$rows=$q->fetchAll(\PDO::FETCH_ASSOC);$ticket['has_more']=count($rows)>5;$ticket['message_page']=$page;$ticket['messages']=array_reverse(array_slice($rows,0,5));return $ticket;
 }
 public function reply(int $admin,int $id,string $body,string $key):void {
  $body=$this->validate($body,$key);$this->pdo->beginTransaction();
  try{
   $q=$this->pdo->prepare("SELECT id FROM admins WHERE id=? AND enabled=1 AND role IN ('owner','moderator') FOR UPDATE");$q->execute([$admin]);if(!$q->fetchColumn())throw new \DomainException('forbidden');
   $q=$this->pdo->prepare('SELECT id FROM support_tickets WHERE id=? FOR UPDATE');$q->execute([$id]);if(!$q->fetchColumn())throw new \DomainException('not_found');
   $q=$this->pdo->prepare('SELECT id FROM support_messages WHERE ticket_id=? AND request_key=?');$q->execute([$id,$key]);if($messageId=$q->fetchColumn()){$q=$this->pdo->prepare('SELECT body,admin_id FROM support_messages WHERE id=?');$q->execute([$messageId]);$previous=$q->fetch(\PDO::FETCH_ASSOC);if($previous['body']!==$body||(int)$previous['admin_id']!==$admin)throw new \InvalidArgumentException('invalid_request');$this->pdo->commit();return;}
   $this->pdo->prepare('INSERT INTO support_messages(ticket_id,admin_id,request_key,body) VALUES (?,?,?,?)')->execute([$id,$admin,$key,$body]);$message=(int)$this->pdo->lastInsertId();
   $this->pdo->prepare("UPDATE support_tickets SET status='answered',updated_at=UTC_TIMESTAMP(6) WHERE id=?")->execute([$id]);$this->audit($admin,$id,'support_reply');$this->pdo->commit();
  }catch(\Throwable $e){if($this->pdo->inTransaction())$this->pdo->rollBack();throw $e;}
  $this->deliver($message);
 }
 public function close(int $admin,int $id):void {
  $q=$this->pdo->prepare("SELECT id FROM admins WHERE id=? AND enabled=1 AND role IN ('owner','moderator')");$q->execute([$admin]);if(!$q->fetchColumn())throw new \DomainException('forbidden');
  $q=$this->pdo->prepare("UPDATE support_tickets SET status='closed',updated_at=UTC_TIMESTAMP(6) WHERE id=? AND status<>'closed'");$q->execute([$id]);if($q->rowCount())$this->audit($admin,$id,'support_close');
 }
 private function audit(int $admin,int $id,string $action):void {
  $this->pdo->prepare("INSERT INTO audit_log(admin_id,action,entity_type,entity_id,reason) VALUES (?,?,'support_ticket',?,'support_inbox')")->execute([$admin,$action,$id]);
 }
 public function deliver(int $message):void {
  // Claim once, commit before SMTP. No automatic resend after uncertain delivery.
  $q=$this->pdo->prepare("UPDATE support_messages SET delivery='sending' WHERE id=? AND delivery='pending'");$q->execute([$message]);if(!$q->rowCount())return;
  $q=$this->pdo->prepare('SELECT m.*,t.user_id,u.email FROM support_messages m JOIN support_tickets t ON t.id=m.ticket_id JOIN users u ON u.id=t.user_id WHERE m.id=?');$q->execute([$message]);$m=$q->fetch(\PDO::FETCH_ASSOC);
  $to=$m['admin_id']===null?(string)($this->config['mail_from']??''):$m['email'];
  try{(new SmtpMailer($this->config))->sendSupport($to,(int)$m['ticket_id'],$m['body'],$m['admin_id']===null);$state='sent';}
  catch(\Throwable){$state='unknown';}
  $this->pdo->prepare('UPDATE support_messages SET delivery=? WHERE id=?')->execute([$state,$message]);
 }
}
