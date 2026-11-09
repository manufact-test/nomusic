<?php
declare(strict_types=1);
namespace Celikom\Admin;
final class AudioGainService
{
 public function __construct(private readonly \PDO $pdo) {}
 public static function value(mixed $raw): float {
  if(!is_string($raw)||!preg_match('/^-?\d{1,2}(?:\.\d)?$/D',$raw))throw new \InvalidArgumentException('invalid_gain');
  $value=(float)$raw;if(!is_finite($value)||$value< -12||$value>12)throw new \InvalidArgumentException('invalid_gain');return round($value,1);
 }
 public function save(array $admin,int $id,mixed $raw,mixed $before):void {
  if(!in_array($admin['role']??null,['owner','moderator'],true))throw new \DomainException('forbidden');
  if($id<1)throw new \InvalidArgumentException('invalid_replacement');
  $gain=self::value($raw);$expected=self::value($before);
  $this->pdo->beginTransaction();
  try {
   $q=$this->pdo->prepare('SELECT gain_db FROM track_replacements WHERE id=? FOR UPDATE');$q->execute([$id]);$old=$q->fetchColumn();
   if($old===false)throw new \DomainException('replacement_missing');
   if(abs((float)$old-$expected)>0.05)throw new \DomainException('gain_changed');
   if(abs((float)$old-$gain)>0.05){
    $this->pdo->prepare('UPDATE track_replacements SET gain_db=? WHERE id=?')->execute([$gain,$id]);
    $this->pdo->prepare("INSERT INTO audit_log(admin_id,action,entity_type,entity_id,reason,before_json,after_json) VALUES(?,'replacement_gain_update','track_replacement',?,'Настройка громкости версии',?,?)")
      ->execute([$admin['id'],$id,json_encode(['gain_db'=>(float)$old],JSON_THROW_ON_ERROR),json_encode(['gain_db'=>$gain],JSON_THROW_ON_ERROR)]);
   }
   $this->pdo->commit();
  }catch(\Throwable $e){if($this->pdo->inTransaction())$this->pdo->rollBack();throw $e;}
 }
}
