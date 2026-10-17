<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * Stage 4 internal editing contract, derived from the approved v10 manifest.
 * This describes fields for future Stage 9 CMS, not a live admin endpoint.
 * Presentation budgets protect approved Header/Hero/demo geometry.
 */
final class FirstScreenFieldCatalog
{
    private const GROUPS = [
        'header' => 'Шапка и навигация',
        'top' => 'Первый экран',
        'sound' => 'Демонстрация звучания',
    ];

    /** Explicit reviewed text budgets, below or equal to generic v10 schema. */
    private const TEXT_LIMITS = [
        'header.text.01' => 28,
        'header.text.02' => 24,
        'header.text.03' => 24,
        'header.text.04' => 24,
        'header.text.05' => 26,
        'hero.eyebrow' => 48,
        'hero.title.first' => 45,
        'hero.title.accent' => 45,
        'hero.lead' => 324,
        'hero.primary.label' => 32,
        'hero.secondary.label' => 36,
        'sound.text.01' => 38,
        'sound.text.02' => 56,
        'sound.text.03' => 326,
        'sound.text.04' => 24,
        'sound.text.05' => 24,
        'sound.text.06' => 38,
        'sound.text.07' => 70,
        'sound.text.08' => 94,
    ];

    /** All allowed link locations are fixed; other page URLs are out of scope. */
    private const LINK_KEYS = [
        'header.link.01', 'header.link.02', 'header.link.03',
        'header.link.04', 'header.link.05',
        'hero.primary.href', 'hero.secondary.href',
    ];

    public const RESTORED_KEY = 'sound.result.restored';
    public const RESTORED_DEFAULT = 'Играет знакомая версия — если она доступна';

    /**
     * @return array<string,array{key:string,section:string,section_label:string,type:string,label:string,default:string,max_chars:int}>
     */
    public static function fields(string $manifestJson): array
    {
        $manifest = json_decode($manifestJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($manifest) || ($manifest['version'] ?? null) !== 1) {
            throw new RuntimeException('Invalid v10 schema');
        }
        $result = [];
        $seenText = [];
        $seenLinks = [];
        foreach (['text_fields' => 'text', 'link_fields' => 'url'] as $bucket => $type) {
            if (!is_array($manifest[$bucket] ?? null)) {
                throw new RuntimeException('Missing v10 manifest bucket');
            }
            foreach ($manifest[$bucket] as $item) {
                if (!is_array($item) || !is_string($item['key'] ?? null) ||
                    !is_string($item['section'] ?? null)) {
                    throw new RuntimeException('Invalid v10 manifest entry');
                }
                $section = $item['section'];
                if (!array_key_exists($section, self::GROUPS)) continue;
                $key = $item['key'];
                $limit = $type === 'text' ? (self::TEXT_LIMITS[$key] ?? null) : 1000;
                if ($limit === null ||
                    $type === 'text' && $limit > ($item['max_chars'] ?? -1) ||
                    $type === 'url' && !in_array($key, self::LINK_KEYS, true) ||
                    isset($result[$key]) || !is_string($item['default'] ?? null)) {
                    throw new RuntimeException('Stage 4 catalog disagrees with approved v10');
                }
                $result[$key] = [
                    'key' => $key, 'section' => $section, 'section_label' => self::GROUPS[$section],
                    'type' => $type,
                    'label' => self::label($key, $item),
                    'default' => $item['default'],
                    'max_chars' => $limit,
                ];
                if ($type === 'text') $seenText[$key] = true;
                else $seenLinks[$key] = true;
            }
        }
        if (count($seenText) !== count(self::TEXT_LIMITS) ||
            count($seenLinks) !== count(self::LINK_KEYS)) {
            throw new RuntimeException('Stage 4 editorial fields missing or changed');
        }
        $result[self::RESTORED_KEY] = [
            'key' => self::RESTORED_KEY, 'section' => 'sound',
            'section_label' => self::GROUPS['sound'],
            'type' => 'demo_state_text', 'label' => 'Подпись: с CELIKOM после переключения',
            'default' => self::RESTORED_DEFAULT, 'max_chars' => 120,
        ];
        return $result;
    }

    /** Only used by CLI previews now; Stage 9 adds editor authentication/CSRF. */
    public static function check(string $key, string $value, array $field): void
    {
        if ($key !== $field['key'] ||
            !in_array($field['type'], ['text', 'url', 'demo_state_text'], true)) {
            throw new InvalidArgumentException('Incorrect editor field');
        }
        if (preg_match('//u', $value) !== 1 ||
            preg_match('/[\x00-\x1F\x7F]/', $value)) {
            throw new InvalidArgumentException('Unsafe editable text encoding');
        }
        $clean = trim($value);
        $length = preg_match_all('/./us', $clean);
        if ($clean === '' || $length === false || $length > $field['max_chars']) {
            throw new InvalidArgumentException('Content exceeds first-screen design budget');
        }
        if ($field['type'] === 'url' && !Content::safeHref($clean)) {
            throw new InvalidArgumentException('Unsafe editor URL');
        }
    }

    private static function label(string $key, array $item): string
    {
        if ($key === 'header.text.01') return 'Название в шапке';
        if ($key === 'hero.title.first') return 'Заголовок — первая строка';
        if ($key === 'hero.title.accent') return 'Заголовок — цветная строка';
        if ($key === 'hero.lead') return 'Подводка первого экрана';
        if ($key === 'hero.primary.href') return 'Основная кнопка — ссылка';
        if ($key === 'hero.secondary.href') return 'Дополнительная кнопка — ссылка';
        if ($key === 'sound.text.07') return 'Подпись: без CELIKOM после переключения';
        $label = trim((string)($item['label'] ?? ''));
        return $label !== '' ? $label : $key;
    }
}
