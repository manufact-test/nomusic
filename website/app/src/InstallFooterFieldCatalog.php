<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * Stage 8 editorial contracts for approved v10 installation, closing CTA
 * and footer. No download/pay link or legal/ownership claim may be invented
 * by a preview editor. Full release-state controls belong to Stage 9+10.
 */
final class InstallFooterFieldCatalog
{
    private const TEXT_LIMITS = [
        'install.text.01' => 54,
        'install.text.02' => 66,
        'closing.text.01' => 22,
        'closing.text.02' => 66,
        'closing.text.03' => 180,
        'closing.text.04' => 35,
        'footer.text.01' => 18,
        'footer.text.02' => 30,
        'footer.text.03' => 30,
        'footer.text.04' => 30,
        'footer.text.05' => 30,
    ];
    /** Must remain truthful until a separately approved real release. */
    private const LOCKED_INSTALL = [
        'install.text.03' => ['проходит тестирование', 'откроем установку'],
        'install.status' => ['Идёт тестирование'],
        'install.text.05' => ['Установка после запуска'],
        'install.text.06' => ['будет готово для', 'проверенный источник'],
        'install.text.07' => ['Пока установка закрыта'],
    ];
    private const LINK_KEYS = [
        'closing.cta.href' => '#top',
        'footer.link.01' => '#top',
        'footer.link.02' => '#how',
        'footer.link.03' => '#contribute',
        'footer.link.04' => '#faq',
        'footer.link.05' => '#install',
    ];

    /** @return array{texts:array<string,array<string,mixed>>,links:array<string,array<string,mixed>>} */
    public static function fields(string $manifestJson): array
    {
        $manifest = json_decode($manifestJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($manifest) || ($manifest['version'] ?? null) !== 1 ||
            !is_array($manifest['text_fields'] ?? null) ||
            !is_array($manifest['link_fields'] ?? null)) {
            throw new RuntimeException('Invalid approved v10 schema');
        }
        $texts = [];
        $locked = [];
        foreach ($manifest['text_fields'] as $field) {
            if (!is_array($field) || !is_string($field['key'] ?? null) ||
                !is_string($field['section'] ?? null)) {
                throw new RuntimeException('Invalid v10 text slot');
            }
            $section = $field['section'];
            if (!in_array($section, ['install','closing','footer'], true)) continue;
            $key = $field['key'];
            if (isset(self::LOCKED_INSTALL[$key])) {
                if (isset($locked[$key]) || !is_string($field['default'] ?? null)) {
                    throw new RuntimeException('Duplicated or invalid installation status');
                }
                $locked[$key] = $field['default'];
                continue;
            }
            $limit = self::TEXT_LIMITS[$key] ?? null;
            if ($limit === null || !is_int($field['max_chars'] ?? null) ||
                $limit > $field['max_chars'] || isset($texts[$key]) ||
                !is_string($field['default'] ?? null) ||
                !is_string($field['label'] ?? null)) {
                throw new RuntimeException('Stage 8 text manifest contract changed');
            }
            $texts[$key] = [
                'key' => $key,
                'type' => 'text',
                'section' => $section,
                'label' => $field['label'],
                'default' => $field['default'],
                'max_chars' => $limit,
            ];
        }
        if (count($texts) !== count(self::TEXT_LIMITS) ||
            count($locked) !== count(self::LOCKED_INSTALL)) {
            throw new RuntimeException('Missing approved Stage 8 text slots');
        }
        foreach (self::LOCKED_INSTALL as $key => $terms) {
            $copy = preg_replace('/\s+/u',' ',str_replace("\u{00A0}",' ', $locked[$key]));
            foreach ($terms as $term) {
                if (!str_contains($copy, $term)) {
                    throw new RuntimeException('Required closed-installation notice changed');
                }
            }
        }
        $links = [];
        foreach ($manifest['link_fields'] as $field) {
            if (!is_array($field) || !is_string($field['key'] ?? null) ||
                !is_string($field['section'] ?? null)) {
                throw new RuntimeException('Invalid v10 link slot');
            }
            if (!in_array($field['section'], ['closing','footer'], true)) continue;
            $key = $field['key'];
            if (!isset(self::LINK_KEYS[$key]) || isset($links[$key]) ||
                ($field['default'] ?? null) !== self::LINK_KEYS[$key]) {
                throw new RuntimeException('Stage 8 navigation registry mismatch');
            }
            $links[$key] = [
                'key' => $key,
                'type' => 'anchor',
                'section' => $field['section'],
                'label' => (string)($field['label'] ?? $key),
                'default' => $field['default'],
            ];
        }
        if (count($links) !== count(self::LINK_KEYS)) {
            throw new RuntimeException('Missing Stage 8 navigation controls');
        }
        return ['texts'=>$texts,'links'=>$links];
    }

    public static function checkText(string $key, string $value, array $field): void
    {
        if (($field['key'] ?? null) !== $key ||
            ($field['type'] ?? null) !== 'text' ||
            preg_match('//u', $value) !== 1 ||
            preg_match('/[\x00-\x1F\x7F]/', $value)) {
            throw new InvalidArgumentException('Invalid Stage 8 text');
        }
        $value = trim($value);
        $count = preg_match_all('/./us', $value);
        if ($value === '' || $count === false ||
            $count > $field['max_chars'] ||
            strlen($value) > $field['max_chars'] * 4) {
            throw new InvalidArgumentException('Stage 8 layout text budget exceeded');
        }
        if ($key === 'closing.text.04' &&
            preg_match('/наверх|вверх|начал[оу]|верхн[юа]/iu', $value) !== 1) {
            throw new InvalidArgumentException('Back-to-top label must describe its destination');
        }
    }

    public static function checkLink(string $key, string $value, array $field, string $template): void
    {
        if (($field['key'] ?? null) !== $key || ($field['type'] ?? null) !== 'anchor' ||
            !isset(self::LINK_KEYS[$key]) || !Content::safeHref($value) ||
            !str_starts_with($value,'#')) {
            throw new InvalidArgumentException('Stage 8 navigation only supports local anchors');
        }
        if ($key === 'closing.cta.href' || $key === 'footer.link.01') {
            if ($value !== '#top') {
                throw new InvalidArgumentException('Back-to-top destination is immutable');
            }
        }
        // Footer navigation is section-level only: never target arbitrary
        // FAQ items, image widgets, admin URLs or private functionality.
        $approvedSections = [
            '#top' => true, '#features' => true, '#how' => true,
            '#sound' => true, '#player' => true, '#contribute' => true,
            '#transparency' => true, '#faq' => true, '#rewards' => true,
            '#install' => true, '#closing' => true,
        ];
        if (!isset($approvedSections[$value]) ||
            substr_count($template, 'id="' . substr($value, 1) . '"') !== 1) {
            throw new InvalidArgumentException('Stage 8 navigation points to a missing target');
        }
    }
}
