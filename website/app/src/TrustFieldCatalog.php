<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * Stage 7: strictly scoped text slots for the approved transparency and FAQ
 * introductions. Legal/product assertions, numbered notes and the FAQ body
 * are NOT free-form marketing fields. This is a future CMS contract only.
 */
final class TrustFieldCatalog
{
    private const LIMITS = [
        'transparency.text.01' => 38,
        'transparency.text.02' => 62,
        'transparency.text.04' => 88,
        'transparency.text.05' => 108,
        'transparency.text.06' => 98,
        'transparency.text.07' => 48,
        'faq.text.01' => 48,
        'faq.text.02' => 62,
        'faq.text.03' => 168,
        'faq.text.04' => 66,
    ];
    private const LOCKED = [
        'transparency.text.03', // not the music service; version conditional
        'transparency.text.08', // no promise of universal restoration
        'transparency.text.09', // fixed item number
        'transparency.text.10', // no arbitrary audio fallback
        'transparency.text.11', // fixed item number
        'transparency.text.12', // mobile is not released
        'transparency.text.13', // fixed item number
        'transparency.text.14', // independence and payouts are not guaranteed
    ];

    /** @return array<string,array<string,mixed>> */
    public static function fields(string $schemaJson): array
    {
        $schema = json_decode($schemaJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($schema) || ($schema['version'] ?? null) !== 1 ||
            !is_array($schema['text_fields'] ?? null)) {
            throw new RuntimeException('Invalid approved v10 schema');
        }
        $fields = [];
        $locked = [];
        foreach ($schema['text_fields'] as $field) {
            if (!is_array($field) || !is_string($field['key'] ?? null) ||
                !is_string($field['section'] ?? null)) {
                throw new RuntimeException('Invalid v10 field definition');
            }
            $key = $field['key'];
            if (!in_array($field['section'], ['transparency', 'faq'], true)) continue;
            if (in_array($key, self::LOCKED, true)) {
                if (isset($locked[$key]) || !is_string($field['default'] ?? null)) {
                    throw new RuntimeException('Malformed locked trust field');
                }
                $locked[$key] = $field['default'];
                continue;
            }
            $limit = self::LIMITS[$key] ?? null;
            if ($limit === null || isset($fields[$key]) ||
                !is_int($field['max_chars'] ?? null) || $limit > $field['max_chars'] ||
                !is_string($field['default'] ?? null)) {
                throw new RuntimeException('Trust editor registry differs from approved v10');
            }
            $fields[$key] = [
                'key' => $key,
                'section' => $field['section'],
                'section_label' => $field['section'] === 'faq' ? 'FAQ — подписи' : 'Доверие',
                'type' => 'text',
                'label' => (string)$field['label'],
                'default' => $field['default'],
                'max_chars' => $limit,
            ];
        }
        if (count($fields) !== count(self::LIMITS) || count($locked) !== count(self::LOCKED)) {
            throw new RuntimeException('Missing v10 Stage 7 slots');
        }
        foreach (['transparency.text.09' => '01',
                  'transparency.text.11' => '02',
                  'transparency.text.13' => '03'] as $key => $value) {
            if ($locked[$key] !== $value) {
                throw new RuntimeException('v10 trust note numbering changed');
            }
        }
        // Defensive consistency check; NOT a legal or payout verification.
        $normalized = [];
        foreach ($locked as $key => $value) {
            $normalized[$key] = preg_replace('/\s+/u', ' ', str_replace("\u{00A0}", ' ', $value));
        }
        foreach ([
            'transparency.text.03' => ['не заменяет', 'проверенная версия'],
            'transparency.text.08' => ['не обещаем'],
            'transparency.text.10' => ['не будет подменять', 'произвольной'],
            'transparency.text.12' => ['отдельная разработка', 'не готовый продукт'],
            'transparency.text.14' => ['независимы', 'не гарантируем'],
        ] as $key => $terms) {
            foreach ($terms as $term) {
                if (!str_contains($normalized[$key], $term)) {
                    throw new RuntimeException('Protected transparency statement changed');
                }
            }
        }
        return $fields;
    }

    public static function check(string $key, string $value, array $field): void
    {
        if (($field['key'] ?? null) !== $key || ($field['type'] ?? null) !== 'text' ||
            preg_match('//u', $value) !== 1 ||
            preg_match('/[\x00-\x1F\x7F]/', $value)) {
            throw new InvalidArgumentException('Invalid Stage 7 content');
        }
        $trimmed = trim($value);
        $chars = preg_match_all('/./us', $trimmed);
        if ($trimmed === '' || $chars === false || $chars > $field['max_chars'] ||
            strlen($trimmed) > $field['max_chars'] * 4) {
            throw new InvalidArgumentException('Stage 7 text exceeds approved layout budget');
        }
    }
}
