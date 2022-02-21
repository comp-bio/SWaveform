<?php
$db = new PDO("sqlite:{$_SERVER['argv'][1]}");

$side = "R";
$start = microtime(true);
$last = microtime(true);
$stmt = $db->prepare("SELECT `s`.`coverage`, `s`.`side` FROM `signal` as `s`, `target` as `t` ".
    "WHERE `t`.`id` = `s`.`target_id` AND `s`.`type` = 'DEL' AND `s`.`side` = '{$side}' AND `t`.`dataset` = 'HGDP'");
$stmt->execute();

$index = 0;
$fb = fopen("__HGDP_DEL_{$side}.bin", 'wb');
while ($item = $stmt->fetch(PDO::FETCH_ASSOC)) {
    fwrite($fb, $item['coverage']);
    $index += 1;
    if ($index % 1000 == 0) {
        $total = microtime(true) - $start;
        $part = (1000/(microtime(true) - $last));
        $next = ((5126269952/1024) - $index)/$part/60/60;
        printf("\ri:{$index}  •  %.2f min.  •  ~%d ips  •  [%.2f H]   ", $total/60, (int)($part), $next);
        $last = microtime(true);
    }
}

fclose($fb);
echo "\r Done!".str_repeat(" ", 80)."\n";
