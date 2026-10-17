<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * Stage 5 readonly field contract for benefits, three-step process and player.
 * All defaults come from the immutable approved v10 registry. This is NOT CMS.
 */
final class PrincipleFieldCatalog
{
    private const SECTIONS = ['features' => 'Преимущества', 'how' => 'Три шага', 'player' => 'Привычный плеер'];
    private const LIMITS = [
        'features.text.01' => 36, 'features.text.02' => 174,
        'features.text.03' => 36, 'features.text.04' => 186,
        'features.text.05' => 36, 'features.text.06' => 178,
        'how.text.01' => 36, 'how.text.02' => 54,
        'how.text.04' => 52, 'how.text.05' => 204,
        'how.text.07' => 52, 'how.text.08' => 138,
        'how.text.10' => 52, 'how.text.11' => 238,
        'player.text.01' => 36, 'player.text.02' => 48,
        'player.text.03' => 48, 'player.text.04' => 312,
        'player.text.05' => 22, 'player.text.06' => 22,
        'player.text.07' => 22, 'player.text.08' => 22,
    ];
    private const FIXED_STEP_NUMBERS = ['how.text.03' => '01', 'how.text.06' => '02', 'how.text.09' => '03'];

    /**
     * @return array<string,array{key:string,section:string,section_label:string,type:string,label:string,default:string,max_chars:int}>
     */
    public static function fields(string $manifestJson): array
    {
        $manifest = json_decode($manifestJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($manifest) || ($manifest['version'] ?? null) !== 1 ||
            !is_array($manifest['text_fields'] ?? null)) {
            throw new RuntimeException('Invalid v10 text manifest');
        }
        $fields = [];
        $fixed = [];
        foreach ($manifest['text_fields'] as $item) {
            if (!is_array($item) || !is_string($item['key'] ?? null) ||
                !is_string($item['section'] ?? null)) {
                throw new RuntimeException('Invalid v10 manifest entry');
            }
            $key = $item['key'];
            $section = $item['section'];
            if (!isset(self::SECTIONS[$section])) continue;
            if (isset(self::FIXED_STEP_NUMBERS[$key])) {
                if (($item['default'] ?? null) !== self::FIXED_STEP_NUMBERS[$key] ||
                    $section !== 'how') {
                    throw new RuntimeException('Stage 5 step numbering changed');
                }
                $fixed[$key] = true;
                continue;
            }
            $budget = self::LIMITS[$key] ?? null;
            if (!is_int($budget) || !is_int($item['max_chars'] ?? null) ||
                $budget > $item['max_chars'] ||
                !is_string($item['default'] ?? null) ||
                isset($fields[$key])) {
                throw new RuntimeException('Stage 5 field drifted from v10');
            }
            $fields[$key] = [
                'key' => $key, 'section' => $section,
                'section_label' => self::SECTIONS[$section],
                'type' => 'text',
                'label' => self::label($key, $item),
                'default' => $item['default'], 'max_chars' => $budget,
            ];
        }
        if (count($fields) !== count(self::LIMITS) ||
            count($fixed) !== count(self::FIXED_STEP_NUMBERS)) {
            throw new RuntimeException('Stage 5 registry missing fields or fixed step labels');
        }
        return $fields;
    }

    public static function check(string $key, string $value, array $field): void
    {
        if ($key !== ($field['key'] ?? null) || ($field['type'] ?? null) !== 'text' ||
            preg_match('//u', $value) !== 1 ||
            preg_match('/[\x00-\x1F\x7F]/', $value)) {
            throw new InvalidArgumentException('Invalid Stage 5 editorial content');
        }
        $value = trim($value);
        $count = preg_match_all('/./us', $value);
        if ($value === '' || $count === false ||
            $count > $field['max_chars'] ||
            strlen($value) > $field['max_chars'] * 4) {
            throw new InvalidArgumentException('Stage 5 text exceeds editorial budget');
        }
    }

    private static function label(string $key, array $item): string
    {
        $labels = [
            'how.text.01' => 'Подпись над шагами',
            'how.text.02' => 'Заголовок блока шагов',
            'how.text.04' => 'Шаг 1 — заголовок',
            'how.text.05' => 'Шаг 1 — описание',
            'how.text.07' => 'Шаг 2 — заголовок',
            'how.text.08' => 'Шаг 2 — описание',
            'how.text.10' => 'Шаг 3 — заголовок',
            'how.text.11' => 'Шаг 3 — описание',
            'player.text.02' => 'Заголовок — первая строка',
            'player.text.03' => 'Заголовок — вторая строка',
        ];
        if (isset($labels[$key])) return $labels[$key];
        $label = trim((string)($item['label'] ?? ''));
        return $label !== '' ? $label : $key;
    }
}
