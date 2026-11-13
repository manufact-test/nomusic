<?php

declare(strict_types=1);

namespace Celikom\Analytics;

final class AnalyticsEventService
{
    public const EVENTS = ['celikom_started', 'celikom_stopped', 'replacement_available', 'replacement_started', 'replacement_completed', 'fail_open', 'manual_original', 'add_track_opened'];
    public const ERRORS = ['api_unavailable', 'media_error', 'play_blocked', 'binding_changed', 'bridge_timeout', 'asset_missing', 'unknown'];

    public function __construct(private readonly EventRepository $repository, private readonly string $privacyKey)
    {
        if (strlen($privacyKey) < 32) {
            throw new \RuntimeException('analytics_not_configured');
        }
    }

    private function keys(array $value, array $allowed): bool
    {
        return count(array_diff(array_keys($value), $allowed)) === 0;
    }

    private function uuid(mixed $value): bool
    {
        return is_string($value) && preg_match('/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/D', $value) === 1;
    }

    public function batch(array $batch): array
    {
        if (!$this->keys($batch, ['schema_version', 'installation_id', 'client_version', 'platform', 'events'])
            || ($batch['schema_version'] ?? null) !== 1 || !$this->uuid($batch['installation_id'] ?? null)
            || !is_string($batch['client_version'] ?? null) || !preg_match('/^\d{1,3}\.\d{1,3}\.\d{1,3}$/D', $batch['client_version'])
            || !in_array($batch['platform'] ?? null, ['chromium', 'android'], true)
            || !is_array($batch['events'] ?? null) || !array_is_list($batch['events']) || count($batch['events']) < 1 || count($batch['events']) > 50) {
            throw new \InvalidArgumentException('invalid_event_batch');
        }
        $hash = hash_hmac('sha256', $batch['installation_id'], $this->privacyKey);
        $results = [];
        foreach ($batch['events'] as $event) {
            $id = is_array($event) && $this->uuid($event['event_id'] ?? null) ? $event['event_id'] : null;
            $valid = $id !== null && $this->keys($event, ['event_id', 'event_name', 'occurred_at', 'properties'])
                && in_array($event['event_name'] ?? null, self::EVENTS, true)
                && is_string($event['occurred_at'] ?? null)
                && preg_match('/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/D', $event['occurred_at']) === 1
                && is_array($event['properties'] ?? null) && $this->keys($event['properties'], ['service', 'error_code']);
            $time = $valid ? strtotime($event['occurred_at']) : false;
            $valid = $valid && $time !== false && gmdate('Y-m-d\TH:i:s', $time) === substr($event['occurred_at'], 0, 19)
                && $time >= time() - 86400 && $time <= time() + 300
                && (!isset($event['properties']['service']) || $event['properties']['service'] === 'yandex')
                && (!isset($event['properties']['error_code']) || in_array($event['properties']['error_code'], self::ERRORS, true));
            if (!$valid) {
                $results[] = ['event_id' => $id, 'status' => 'rejected', 'error' => 'invalid_event'];
                continue;
            }
            $stored = $event + ['installation_hash' => $hash, 'client_version' => $batch['client_version'], 'platform' => $batch['platform']];
            $stored['occurred_at'] = gmdate('Y-m-d H:i:s', $time);
            $results[] = ['event_id' => $id, 'status' => $this->repository->insert($stored) ? 'accepted' : 'duplicate'];
        }
        return ['schema_version' => 1, 'results' => $results];
    }
}
