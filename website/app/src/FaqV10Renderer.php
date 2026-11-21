<?php
declare(strict_types=1);

namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * A complete data-to-markup vertical slice for the approved CELIKOM v10 FAQ.
 *
 * A Stage 9 administrator will store an authorized FAQ revision and pass it to
 * this class. Nothing in this class reads, writes or publishes a database.
 *
 * The original FAQ is verified against the seed and returned byte-for-byte
 * unchanged when no FAQ changes are requested. All HTML generated for edited
 * questions/answers is plain text escaped into the original trusted skeleton.
 */
final class FaqV10Renderer
{
    private const MAX_ITEMS = 100;
    private const MAX_QUESTION_CHARS = 400;
    private const MAX_ANSWER_CHARS = 3000;
    private const ITEM_PATTERN = '~<details class="faq-item" data-category="([a-z]+)" id="(faq-question-[0-9]{2,4})"><summary><span>(.*?)</span>(<svg aria-hidden="true" viewbox="0 0 24 24"><path d="M12 5v14M5 12h14"></path></svg>)</summary><div class="answer">(<p>[^<>]*</p>)</div></details>~us';

    /**
     * Draft format:
     * {"updates":{"faq-question-01":{"question":"...","answer":"...","category":"music","sort_order":15,"is_visible":true}},
     *  "new_items":[{"id":"faq-question-29","category":"start","question":"...","answer":"...","sort_order":290,"is_visible":true}]}
     *
     * Plain-text answer is used for editing. Existing seed's answer_html is
     * trusted only after exact verification against unchanged v10 source.
     *
     * @param array<string,mixed> $draft
     */
    public static function render(string $html, string $seedJson, array $draft = []): string
    {
        $seed = json_decode($seedJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($seed) || ($seed['version'] ?? null) !== 1 ||
            !is_array($seed['items'] ?? null) || !is_array($seed['categories'] ?? null)) {
            throw new RuntimeException('Invalid FAQ v10 seed');
        }
        [$block, $offset, $length] = self::extractList($html);
        preg_match_all(self::ITEM_PATTERN, $block, $match, PREG_SET_ORDER | PREG_OFFSET_CAPTURE);
        $items = $seed['items'];
        if (count($match) !== 28 || count($items) !== 28) {
            throw new RuntimeException('Approved FAQ reference must contain exactly 28 entries');
        }
        $defaultMarkup = '';
        $verified = [];
        foreach ($items as $i => $item) {
            if (!is_array($item) ||
                !isset($item['id'], $item['category'], $item['question'], $item['answer_html'], $item['sort_order'], $item['is_visible']) ||
                $match[$i][0][1] !== strlen($defaultMarkup) ||
                $match[$i][1][0] !== $item['category'] ||
                $match[$i][2][0] !== $item['id'] ||
                $match[$i][3][0] !== $item['question'] ||
                $match[$i][5][0] !== $item['answer_html'] ||
                $item['sort_order'] !== ($i + 1) * 10 ||
                $item['is_visible'] !== true) {
                throw new RuntimeException('FAQ seed differs from the approved v10 markup');
            }
            if (isset($verified[$item['id']])) {
                throw new RuntimeException('Duplicate approved FAQ ID');
            }
            $original = $match[$i][0][0];
            $defaultMarkup .= $original;
            $verified[$item['id']] = [
                'id' => $item['id'],
                'category' => $item['category'],
                'question' => $item['question'],
                'answer' => substr($item['answer_html'], 3, -4),
                'sort_order' => $item['sort_order'],
                'is_visible' => true,
                'original' => $original,
                'svg' => $match[$i][4][0],
                'initial_index' => $i,
            ];
        }
        if ($defaultMarkup !== $block) {
            throw new RuntimeException('FAQ v10 contains unexpected additional markup');
        }

        // In particular, reject edits to category definitions, JS filter IDs
        // and arbitrary top-level payload keys. That needs its own UI review.
        foreach (array_keys($draft) as $name) {
            if ($name !== 'updates' && $name !== 'new_items') {
                throw new InvalidArgumentException('Unknown FAQ draft operation');
            }
        }
        if ($draft === [] || (($draft['updates'] ?? []) === [] && ($draft['new_items'] ?? []) === [])) {
            return $html;
        }

        $categories = [];
        foreach ($seed['categories'] as $category) {
            if (!is_array($category) || !isset($category['key'], $category['is_visible']) ||
                !is_string($category['key']) || !$category['is_visible']) {
                throw new RuntimeException('Invalid FAQ category schema');
            }
            $categories[$category['key']] = true;
        }
        if (array_keys($categories) !== ['start', 'rewards', 'music', 'help']) {
            throw new RuntimeException('Unexpected FAQ filter categories');
        }

        $updates = $draft['updates'] ?? [];
        $created = $draft['new_items'] ?? [];
        if (!is_array($updates) || !is_array($created) || !array_is_list($created) ||
            count($created) + count($verified) > self::MAX_ITEMS) {
            throw new InvalidArgumentException('Invalid FAQ item collection');
        }

        foreach ($updates as $id => $fields) {
            if (!is_string($id) || !isset($verified[$id]) || !is_array($fields)) {
                throw new InvalidArgumentException('Unknown FAQ item to update');
            }
            $verified[$id] = self::mergeItem($verified[$id], $fields, $categories);
        }

        $index = count($verified);
        foreach ($created as $new) {
            if (!is_array($new) || !isset($new['id']) || !is_string($new['id']) ||
                !preg_match('~^faq-question-[0-9]{2,4}$~D', $new['id']) ||
                isset($verified[$new['id']])) {
                throw new InvalidArgumentException('Invalid or duplicate new FAQ ID');
            }
            $required = ['category','question','answer','sort_order','is_visible'];
            if (array_diff($required, array_keys($new)) !== [] ||
                array_diff(array_keys($new), array_merge(['id'], $required)) !== []) {
                throw new InvalidArgumentException('Missing or unknown new FAQ field');
            }
            $base = [
                'id' => $new['id'],
                'category' => 'start',
                'question' => 'placeholder',
                'answer' => 'placeholder',
                'sort_order' => 0,
                'is_visible' => true,
                'original' => '',
                'svg' => $match[0][4][0],
                'initial_index' => $index++,
            ];
            $verified[$new['id']] = self::mergeItem($base, array_intersect_key($new, array_flip($required)), $categories);
        }

        $ordered = array_values(array_filter($verified, static fn(array $item): bool => $item['is_visible']));
        usort($ordered, static fn(array $a, array $b): int =>
            ($a['sort_order'] <=> $b['sort_order']) ?: ($a['initial_index'] <=> $b['initial_index'])
        );
        $rendered = '';
        foreach ($ordered as $item) {
            $default = $items[$item['initial_index']] ?? null;
            if ($item['original'] !== '' && $default !== null &&
                $item['category'] === $default['category'] &&
                $item['question'] === $default['question'] &&
                $item['answer'] === substr($default['answer_html'], 3, -4)) {
                $rendered .= $item['original'];
                continue;
            }
            // No new SVG, scripts, event handlers, CSS, HTML or images from data.
            $rendered .= '<details class="faq-item" data-category="' . $item['category'] .
                '" id="' . $item['id'] . '"><summary><span>' .
                Content::escape($item['question']) . '</span>' . $item['svg'] .
                '</summary><div class="answer"><p>' . Content::escape($item['answer']) .
                '</p></div></details>';
        }

        return substr_replace($html, $rendered, $offset, $length);
    }

    /**
     * @return array{string,int,int}
     */
    private static function extractList(string $html): array
    {
        $prefix = '<div class="faq-list" id="faq-list">';
        $start = strpos($html, $prefix);
        if ($start === false || strpos($html, $prefix, $start + 1) !== false) {
            throw new RuntimeException('FAQ list wrapper is missing or duplicated');
        }
        $start += strlen($prefix);
        $end = strpos($html, '</div><div class="faq-empty" hidden="" id="faq-empty">', $start);
        if ($end === false || $end <= $start) {
            throw new RuntimeException('Unexpected FAQ list closing structure');
        }
        return [substr($html, $start, $end - $start), $start, $end - $start];
    }

    /**
     * @param array<string,mixed> $original
     * @param array<string,mixed> $fields
     * @param array<string,bool> $categories
     * @return array<string,mixed>
     */
    private static function mergeItem(array $original, array $fields, array $categories): array
    {
        $editable = ['category' => true,'question' => true,'answer' => true,'sort_order' => true,'is_visible' => true];
        foreach ($fields as $key => $value) {
            if (!is_string($key) || !isset($editable[$key])) {
                throw new InvalidArgumentException('Uneditable FAQ field');
            }
            if ($key === 'category') {
                if (!is_string($value) || !isset($categories[$value])) {
                    throw new InvalidArgumentException('Unknown FAQ category');
                }
            } elseif ($key === 'question' || $key === 'answer') {
                if (!is_string($value)) {
                    throw new InvalidArgumentException('FAQ content must be text');
                }
                $value = self::plainText($value, $key === 'question' ? self::MAX_QUESTION_CHARS : self::MAX_ANSWER_CHARS);
            } elseif ($key === 'sort_order') {
                if (!is_int($value) || $value < 0 || $value > 100000) {
                    throw new InvalidArgumentException('Invalid FAQ sort order');
                }
            } elseif (!is_bool($value)) {
                throw new InvalidArgumentException('FAQ visibility must be Boolean');
            }
            $original[$key] = $value;
        }
        return $original;
    }

    private static function plainText(string $value, int $max): string
    {
        if (preg_match('//u', $value) !== 1) {
            throw new InvalidArgumentException('FAQ text must be valid UTF-8');
        }
        $value = trim($value);
        if ($value === '' || strlen($value) > 4 * $max ||
            preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', $value)) {
            throw new InvalidArgumentException('Empty or invalid FAQ text');
        }
        $chars = preg_match_all('/./us', $value);
        if ($chars === false || $chars > $max) {
            throw new InvalidArgumentException('Oversized FAQ content');
        }
        return $value;
    }
}
