<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * Stage 3, v10 only: safely replace approved content text/links in a trusted
 * HTML template. No markup is parsed and serialized (which could change
 * visuals); fixed ranges from the canonical template are updated instead.
 *
 * No untrusted HTML, arbitrary media URLs or CMS data are accepted here.
 * Stage 9 must feed this exclusively from authorized revisions/snapshots.
 */
final class V10Renderer
{
    /**
     * @param array<string, mixed> $overrides Plain UTF-8 text and links only.
     */
    public static function render(string $html, string $manifestJson, array $overrides = []): string
    {
        $manifest = json_decode($manifestJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($manifest) || ($manifest['version'] ?? null) !== 1) {
            throw new RuntimeException('Invalid content schema');
        }
        // Immutable visual template: a changed HTML structure requires a new
        // reviewed manifest, not guesswork when replacing visible content.
        $blobSha = sha1('blob ' . strlen($html) . "\0" . $html);
        if (!hash_equals((string)($manifest['template_git_blob_sha'] ?? ''), $blobSha)) {
            throw new RuntimeException('Visual template does not match the approved content schema');
        }

        $textMap = self::indexedFields($manifest['text_fields'] ?? null, 'ordinal');
        $linkMap = self::indexedFields($manifest['link_fields'] ?? null, 'element_ordinal');
        $attributeFields = $manifest['attribute_fields'] ?? [];
        if (!is_array($attributeFields) || count($attributeFields) !== 2) {
            throw new RuntimeException('Missing SEO and accessible media metadata');
        }
        $allowed = [];
        foreach (array_merge(array_values($textMap), array_values($linkMap), $attributeFields) as $field) {
            $allowed[$field['key']] = $field;
        }
        foreach ($overrides as $key => $value) {
            if (!is_string($key) || !isset($allowed[$key])) {
                throw new InvalidArgumentException('Unknown or non-editable content key');
            }
            if (!is_string($value) || preg_match('//u', $value) !== 1) {
                throw new InvalidArgumentException('Content must be UTF-8 text');
            }
        }
        if ($overrides === []) {
            // Still run template/schema compatibility guards on first read.
            self::verifyFields($html, $textMap, $linkMap, $attributeFields);
            return $html;
        }

        $replacements = [];
        if (preg_match_all('~<!--[\s\S]*?-->|<![^>]*>|</?[A-Za-z][^>]*>|[^<]+~u', $html, $matches, PREG_OFFSET_CAPTURE) === false) {
            throw new RuntimeException('Cannot parse trusted HTML tokens');
        }
        $i = 0;
        $seen = [];
        foreach ($matches[0] as [$raw, $byteOffset]) {
            if ($raw === '' || $raw[0] === '<' || trim($raw) === '') {
                continue;
            }
            $i++;
            if (!isset($textMap[$i])) {
                continue;
            }
            $field = $textMap[$i];
            if ($raw !== $field['default']) {
                throw new RuntimeException('Content slot changed: ' . $field['key']);
            }
            $seen[$field['key']] = true;
            if (!array_key_exists($field['key'], $overrides)) {
                continue;
            }
            $replacement = self::validText($overrides[$field['key']], (int) $field['max_chars']);
            // A normal CMS save of an unchanged value must not change typography.
            if ($replacement === trim($raw)) {
                continue;
            }
            if (!preg_match('/^(\s*)(.*?)(\s*)$/us', $raw, $parts)) {
                throw new RuntimeException('Invalid text token');
            }
            $replacements[] = [
                'offset' => $byteOffset,
                'length' => strlen($raw),
                'html' => $parts[1] . Content::escape($replacement) . $parts[3],
            ];
        }
        if (preg_match_all('~<a\b[^>]*>~u', $html, $anchors, PREG_OFFSET_CAPTURE) === false) {
            throw new RuntimeException('Cannot identify link controls');
        }
        foreach ($linkMap as $ordinal => $field) {
            if (!isset($anchors[0][$ordinal - 1])) {
                throw new RuntimeException('Missing link element: ' . $field['key']);
            }
            [$raw, $byteOffset] = $anchors[0][$ordinal - 1];
            $needle = 'href="' . $field['default'] . '"';
            if (substr_count($raw, $needle) !== 1) {
                throw new RuntimeException('Original link mismatch: ' . $field['key']);
            }
            $seen[$field['key']] = true;
            if (!array_key_exists($field['key'], $overrides)) {
                continue;
            }
            $value = $overrides[$field['key']];
            if (strlen($value) > 1000 || !Content::safeHref($value)) {
                throw new InvalidArgumentException('Unsafe CMS link');
            }
            if ($value === $field['default']) {
                continue;
            }
            $newTag = str_replace($needle, 'href="' . Content::escape($value) . '"', $raw);
            $replacements[] = ['offset' => $byteOffset, 'length' => strlen($raw), 'html' => $newTag];
        }
        self::applyAttributes($html, $attributeFields, $overrides, $seen, $replacements);
        if (count($seen) !== count($textMap) + count($linkMap) + count($attributeFields)) {
            throw new RuntimeException('CMS registry and template token positions differ');
        }
        usort($replacements, static fn(array $a, array $b): int => $b['offset'] <=> $a['offset']);
        foreach ($replacements as $change) {
            $html = substr_replace($html, $change['html'], $change['offset'], $change['length']);
        }
        return $html;
    }


    /**
     * Only two literal-approved attribute types are editable in Stage 3:
     * SEO description and popup accessibility text. Never render arbitrary
     * tag names, CSS, media URLs or event attributes from a CMS schema.
     *
     * @param array<int,array<string,mixed>> $attributeFields
     * @param array<string,mixed> $overrides
     * @param array<string,bool> $seen
     * @param array<int,array<string,int|string>> $replacements
     */
    private static function applyAttributes(
        string $html,
        array $attributeFields,
        array $overrides,
        array &$seen,
        array &$replacements
    ): void {
        $allowed = [
            'seo.description' => ['meta', 4, 'content'],
            'media.popup.alt' => ['img', 3, 'alt'],
        ];
        foreach ($attributeFields as $field) {
            $key = $field['key'] ?? null;
            $spec = $allowed[$key] ?? null;
            if ($spec === null || ($field['tag'] ?? null) !== $spec[0] ||
                ($field['element_ordinal'] ?? null) !== $spec[1] ||
                ($field['attribute'] ?? null) !== $spec[2] ||
                !is_string($field['default'] ?? null)) {
                throw new RuntimeException('Unapproved editable attribute');
            }
            $tag = $spec[0];
            preg_match_all('~<' . $tag . '\b[^>]*>~u', $html, $tags, PREG_OFFSET_CAPTURE);
            if (!isset($tags[0][$spec[1] - 1])) {
                throw new RuntimeException('Missing editable metadata tag');
            }
            [$original, $offset] = $tags[0][$spec[1] - 1];
            $needle = $spec[2] . '="' . $field['default'] . '"';
            if (substr_count($original, $needle) !== 1) {
                throw new RuntimeException('Metadata content has changed');
            }
            $seen[$key] = true;
            if (!array_key_exists($key, $overrides)) {
                continue;
            }
            $new = self::validText($overrides[$key], (int) $field['max_chars']);
            if ($new === $field['default']) {
                continue;
            }
            $replacements[] = [
                'offset' => $offset,
                'length' => strlen($original),
                'html' => str_replace(
                    $needle,
                    $spec[2] . '="' . Content::escape($new) . '"',
                    $original
                ),
            ];
        }
    }

    /** @return array<int,array<string,mixed>> */
    private static function indexedFields(mixed $fields, string $ordinalName): array
    {
        if (!is_array($fields)) {
            throw new RuntimeException('Missing content registry fields');
        }
        $out = [];
        $keys = [];
        foreach ($fields as $field) {
            if (!is_array($field) || !isset($field['key'], $field[$ordinalName], $field['default'])) {
                throw new RuntimeException('Malformed content registry field');
            }
            $index = $field[$ordinalName];
            if (!is_int($index) || $index < 1 || isset($out[$index]) || isset($keys[$field['key']])) {
                throw new RuntimeException('Duplicate or invalid content registry slot');
            }
            $out[$index] = $field;
            $keys[$field['key']] = true;
        }
        return $out;
    }

    private static function validText(string $value, int $maxChars): string
    {
        $value = trim($value);
        if ($value === '' || $maxChars < 1 || strlen($value) > $maxChars * 4) {
            throw new InvalidArgumentException('Empty or oversized content');
        }
        $chars = preg_match_all('/./us', $value);
        if ($chars === false || $chars > $maxChars) {
            throw new InvalidArgumentException('Content exceeds field length');
        }
        if (preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', $value)) {
            throw new InvalidArgumentException('Control character in text');
        }
        return $value;
    }

    /**
     * Check that the manifest anchors every editable node to unchanged v10
     * source, even when no content override is requested.
     *
     * @param array<int,array<string,mixed>> $textMap
     * @param array<int,array<string,mixed>> $linkMap
     */
    private static function verifyFields(string $html, array $textMap, array $linkMap, array $attributeFields): void
    {
        $n = preg_match_all('~<!--[\s\S]*?-->|<![^>]*>|</?[A-Za-z][^>]*>|[^<]+~u', $html, $matches);
        if ($n === false) {
            throw new RuntimeException('Invalid template');
        }
        $ordinal = 0;
        $count = 0;
        foreach ($matches[0] as $raw) {
            if ($raw === '' || $raw[0] === '<' || trim($raw) === '') {
                continue;
            }
            $ordinal++;
            if (isset($textMap[$ordinal])) {
                if ($raw !== $textMap[$ordinal]['default']) {
                    throw new RuntimeException('Text registry mismatch');
                }
                $count++;
            }
        }
        if ($count !== count($textMap)) {
            throw new RuntimeException('Missing text registry slots');
        }
        preg_match_all('~<a\b[^>]*>~u', $html, $links);
        foreach ($linkMap as $ordinal => $field) {
            if (!isset($links[0][$ordinal - 1]) ||
                substr_count($links[0][$ordinal - 1], 'href="' . $field['default'] . '"') !== 1) {
                throw new RuntimeException('Link registry mismatch');
            }
        }
        $seen = [];
        $unused = [];
        self::applyAttributes($html, $attributeFields, [], $seen, $unused);
    }
}
