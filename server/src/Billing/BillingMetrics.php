<?php

declare(strict_types=1);

namespace Celikom\Billing;

use PDO;

/** Confirmed ledger totals, in integer minor units; currencies are never added. */
final class BillingMetrics
{
    public function __construct(private readonly PDO $pdo) {}

    public function forPeriod(string $from, string $to): array
    {
        $start=\DateTimeImmutable::createFromFormat('!Y-m-d',$from,new \DateTimeZone('Europe/Moscow'));
        $end=\DateTimeImmutable::createFromFormat('!Y-m-d',$to,new \DateTimeZone('Europe/Moscow'));
        if (!$start || !$end || $start->format('Y-m-d')!==$from || $end->format('Y-m-d')!==$to
            || $end<$start || $start->diff($end)->days>366) throw new \InvalidArgumentException('invalid_billing_dates');
        $right=\Celikom\Support\MoscowTime::utc($end->modify('+1 day'));
        $left=\Celikom\Support\MoscowTime::utc($start);
        $q=$this->pdo->prepare("SELECT currency,SUM(gross_minor) AS gross_minor,
            SUM(refund_minor) AS refund_minor,SUM(chargeback_minor) AS chargeback_minor,
            SUM(payment_count) AS payment_count,SUM(first_count) AS first_count FROM (
                SELECT p.currency,p.amount_minor AS gross_minor,0 AS refund_minor,0 AS chargeback_minor,
                    1 AS payment_count,
                    NOT EXISTS(SELECT 1 FROM billing_payments prior WHERE prior.subscription_id=p.subscription_id
                        AND (prior.valid_from<p.valid_from OR (prior.valid_from=p.valid_from AND prior.id<p.id))) AS first_count
                FROM billing_payments p JOIN billing_events e ON e.id=p.event_id
                WHERE e.occurred_at>=? AND e.occurred_at<?
                UNION ALL
                SELECT p.currency,0,IF(a.kind='refund',a.amount_minor,0),IF(a.kind='chargeback',a.amount_minor,0),0,0
                FROM billing_adjustments a JOIN billing_payments p ON p.id=a.payment_id
                JOIN billing_events e ON e.id=a.event_id WHERE e.occurred_at>=? AND e.occurred_at<?
            ) entries GROUP BY currency ORDER BY currency");
        $q->execute([$left,$right,$left,$right]);$currencies=[];
        foreach($q->fetchAll(PDO::FETCH_ASSOC) as $row) {
            foreach(['gross_minor','refund_minor','chargeback_minor','payment_count','first_count'] as $field)
                $row[$field]=(int)$row[$field];
            $row['after_adjustments_minor']=$row['gross_minor']-$row['refund_minor']-$row['chargeback_minor'];
            $row['renewal_count']=$row['payment_count']-$row['first_count'];
            $currencies[]=$row;
        }
        return ['from'=>$from,'to'=>$to,'timezone'=>'Europe/Moscow','currencies'=>$currencies,
            'fees_available'=>false,'net_revenue_available'=>false];
    }
}
