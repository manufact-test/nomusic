<?php
declare(strict_types=1);
ini_set('display_errors','0');
try {
    $base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release=realpath($base.'/current');
    if (!is_link($base.'/current') || !is_string($release) || !str_starts_with($release,$base.'/releases/')
        || !is_file($release.'/bootstrap.php')) throw new RuntimeException('bad_release');
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    $pdo=\Celikom\Database\Connection::open($config);
    $candidates=json_decode(<<<'TRACKS'
[
  {
    "id": "63104735",
    "artist": "ZOVetik, Nemichieff",
    "title": "Отключили свет"
  },
  {
    "id": "137472446",
    "artist": "голодный",
    "title": "таблетки"
  },
  {
    "id": "150598645",
    "artist": "uglystephan",
    "title": "Я люблю лин"
  },
  {
    "id": "145054524",
    "artist": "Пошлая Молли",
    "title": "Спать с тобой"
  },
  {
    "id": "136272297",
    "artist": "9mice",
    "title": "indiana"
  },
  {
    "id": "123382745",
    "artist": "Серега Пират",
    "title": "В этой траве"
  },
  {
    "id": "138778164",
    "artist": "KSB muzic",
    "title": "Отчим"
  },
  {
    "id": "155025088",
    "artist": "Clonnex",
    "title": "ILD"
  },
  {
    "id": "137300017",
    "artist": "madk1d",
    "title": "так похуй"
  },
  {
    "id": "93401053",
    "artist": "Паша Техник",
    "title": "Я ебал в рот"
  },
  {
    "id": "151855603",
    "artist": "CUPSIZE",
    "title": "мы делили апельсин"
  },
  {
    "id": "91340238",
    "artist": "Пошлая Молли, Элджей",
    "title": "Дом Периньон"
  },
  {
    "id": "152396542",
    "artist": "Пошлая Молли",
    "title": "Lin Ansty"
  },
  {
    "id": "136404135",
    "artist": "Пошлая Молли",
    "title": "Школа не нужна"
  },
  {
    "id": "138629224",
    "artist": "Расстройство",
    "title": "Виновата скорость"
  },
  {
    "id": "110374527",
    "artist": "Lida, СТИНТ, mazzellovvv, ШАПКА, t2x2, Барагозеры",
    "title": "Новогодняя"
  },
  {
    "id": "149870633",
    "artist": "Синдром Восьмиклассника",
    "title": "ДЖЕТИКС"
  },
  {
    "id": "30212997",
    "artist": "Yanix, ATL",
    "title": "Трэп хата"
  },
  {
    "id": "111001121",
    "artist": "две тысячи ярдов",
    "title": "Постарели"
  },
  {
    "id": "120305632",
    "artist": "CUPSIZE",
    "title": "Клей"
  },
  {
    "id": "63607797",
    "artist": "4К",
    "title": "Крайне аккуратно"
  },
  {
    "id": "59357625",
    "artist": "Сява",
    "title": "Меня вставляет дым"
  },
  {
    "id": "139910364",
    "artist": "тёмный принц",
    "title": "губы"
  },
  {
    "id": "63607783",
    "artist": "4К",
    "title": "Если чё"
  },
  {
    "id": "25319594",
    "artist": "Anacondaz",
    "title": "Мама, я люблю"
  },
  {
    "id": "111402809",
    "artist": "Kai Angel, 9mice",
    "title": "LIPSTICK"
  },
  {
    "id": "88057589",
    "artist": "zavet",
    "title": "Вот она"
  },
  {
    "id": "63607809",
    "artist": "4К",
    "title": "Хули нет"
  },
  {
    "id": "113240879",
    "artist": "Lizer",
    "title": "Не ангел"
  },
  {
    "id": "63607788",
    "artist": "4К",
    "title": "Милиция"
  },
  {
    "id": "144622062",
    "artist": "тёмный принц",
    "title": "скидка"
  },
  {
    "id": "133951915",
    "artist": "Kai Angel",
    "title": "madam"
  },
  {
    "id": "109996936",
    "artist": "CMH, GSPD, Lida",
    "title": "Сумасшедшая"
  },
  {
    "id": "115131527",
    "artist": "ЗимойБезШапки",
    "title": "Лёха"
  },
  {
    "id": "136901411",
    "artist": "madk1d, тёмный принц",
    "title": "ты че обиделась"
  }
]
TRACKS
, true, 16, JSON_THROW_ON_ERROR);
    if(count($candidates)!==35) throw new RuntimeException('wrong_candidate_count');
    $pdo->exec('START TRANSACTION READ ONLY');
    $exact=$pdo->prepare("SELECT r.status,r.is_active FROM tracks t LEFT JOIN track_replacements r ON r.track_id=t.id WHERE t.service='yandex' AND t.service_track_id=? LIMIT 1");
    $requests=$pdo->prepare("SELECT id FROM track_requests WHERE service='yandex' AND service_track_id=? LIMIT 1");
    $same=$pdo->prepare("SELECT service_track_id FROM tracks WHERE service='yandex' AND LOWER(TRIM(artist))=LOWER(TRIM(?)) AND LOWER(TRIM(title))=LOWER(TRIM(?)) LIMIT 1");
    $available=[]; $skipped=[];
    foreach($candidates as $e){
      if(!preg_match('/^[1-9][0-9]{0,19}$/D',$e['id'])) throw new RuntimeException('bad_id');
      $exact->execute([$e['id']]); $found=$exact->fetch(PDO::FETCH_ASSOC);
      $requests->execute([$e['id']]);$rq=$requests->fetchColumn();
      $same->execute([$e['artist'],$e['title']]);$other=$same->fetchColumn();
      if($found || $rq!==false || $other!==false){
         $skipped[]=['id'=>$e['id'],'reason'=>$found?'track_exists':($rq!==false?'request_exists':'title_exists')];
      }else{ $available[]=['id'=>$e['id'],'artist'=>$e['artist'],'title'=>$e['title']]; }
    }
    $pdo->rollBack();
    echo json_encode(['status'=>'READ_ONLY_PASS','total'=>count($candidates),'eligible'=>count($available),'eligible_candidates'=>$available,'excluded'=>$skipped,'writes'=>0],JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR)."\n";
}catch(Throwable $error){
    if(isset($pdo) && $pdo instanceof PDO && $pdo->inTransaction())$pdo->rollBack();
    fwrite(STDERR,'READ_ONLY_FAILED: '.get_class($error).'\n');exit(1);
}
