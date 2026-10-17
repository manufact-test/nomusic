<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * Stage 6 community: safe editor preview without any CMS/API endpoint.
 * Critical money, rights and moderation promises remain fixed pending Stage 9.
 */
final class CommunityFieldCatalog
{
    private const LIMITS = [
        'contribute.text.01' => 38,
        'contribute.text.02' => 50,
        'contribute.text.03' => 50,
        'contribute.text.04' => 246,
        'contribute.text.05' => 40,
        'contribute.text.06' => 222,
        'contribute.text.07' => 40,
        'contribute.text.08' => 270,
        'rewards.text.01' => 38,
        'rewards.text.02' => 76,
    ];

    /** No editing the promise of 2%/20%/10/carry-forward, or payment readiness. */
    private const LOCKED = ['rewards.text.03', 'rewards.text.04'];

    /** @return array<string,array<string,mixed>> */
    public static function fields(string $schemaJson): array
    {
        $schema = json_decode($schemaJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($schema) || ($schema['version'] ?? null) !== 1 ||
            !is_array($schema['text_fields'] ?? null)) {
            throw new RuntimeException('Invalid approved v10 schema');
        }
        $result = [];
        $lockedSeen = [];
        foreach ($schema['text_fields'] as $field) {
            if (!is_array($field) || !is_string($field['key'] ?? null) ||
                !is_string($field['section'] ?? null)) {
                throw new RuntimeException('Invalid v10 field');
            }
            $key = $field['key'];
            $section = $field['section'];
            if (!in_array($section, ['contribute', 'rewards'], true)) continue;
            if (in_array($key, self::LOCKED, true)) {
                $lockedSeen[$key] = $field['default'] ?? null;
                continue;
            }
            $max = self::LIMITS[$key] ?? null;
            if ($max === null || !is_int($field['max_chars'] ?? null) ||
                $max > $field['max_chars'] ||
                !is_string($field['default'] ?? null) ||
                isset($result[$key])) {
                throw new RuntimeException('Community editorial registry changed');
            }
            $result[$key] = [
                'key' => $key,
                'section' => $section,
                'section_label' => $section === 'contribute' ? 'Участие сообщества' : 'Бонусы',
                'type' => 'text',
                'label' => self::label($key),
                'default' => $field['default'],
                'max_chars' => $max,
            ];
        }
        if (count($result) !== count(self::LIMITS) ||
            count($lockedSeen) !== count(self::LOCKED)) {
            throw new RuntimeException('Missing expected Stage 6 v10 slots');
        }
        // This is a guard on existing approved copy, not verification of live
        // entitlement logic in the extension/server. Keep those systems apart.
        $rule = preg_replace('/\s+/u', ' ', (string)$lockedSeen['rewards.text.03']);
        $notice = preg_replace('/\s+/u', ' ', (string)$lockedSeen['rewards.text.04']);
        if (!str_contains($rule, '2%') || !str_contains($rule, '20%') ||
            !str_contains($rule, '10 песен') || !str_contains($rule, 'следующие месяцы') ||
            !str_contains($notice, 'до запуска оплаты') ||
            !str_contains($notice, 'когда платежи заработают')) {
            throw new RuntimeException('Approved reward and payment facts changed');
        }
        return $result;
    }

    public static function check(string $key, string $value, array $field): void
    {
        if (($field['key'] ?? null) !== $key || ($field['type'] ?? null) !== 'text' ||
            preg_match('//u', $value) !== 1 ||
            preg_match('/[\x00-\x1F\x7F]/', $value)) {
            throw new InvalidArgumentException('Invalid community editor value');
        }
        $value = trim($value);
        $length = preg_match_all('/./us', $value);
        if ($value === '' || $length === false || $length > $field['max_chars'] ||
            strlen($value) > $field['max_chars'] * 4) {
            throw new InvalidArgumentException('Community text exceeds v10 layout budget');
        }
    }

    private static function label(string $key): string
    {
        $labels = [
            'contribute.text.01' => 'Участие — верхняя подпись',
            'contribute.text.02' => 'Участие — заголовок, первая строка',
            'contribute.text.03' => 'Участие — заголовок, вторая строка',
            'contribute.text.04' => 'Участие — пояснение',
            'contribute.text.05' => 'Предложить песню — заголовок',
            'contribute.text.06' => 'Предложить песню — описание',
            'contribute.text.07' => 'Загрузить версию — заголовок',
            'contribute.text.08' => 'Загрузить версию — описание и права',
            'rewards.text.01' => 'Бонусы — верхняя подпись',
            'rewards.text.02' => 'Бонусы — заголовок',
        ];
        return $labels[$key] ?? $key;
    }
}
