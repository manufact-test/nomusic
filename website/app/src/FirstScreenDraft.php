<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * Stage 4 isolated editorial contract for the accepted v10 first impression:
 * header, hero and visual-only sound demonstration.
 *
 * This is NOT a CMS route or a trusted authorization boundary. Stage 9 must
 * authenticate the editor and verify CSRF before calling this helper.
 */
final class FirstScreenDraft
{
    private const SECTIONS = ['header' => true, 'top' => true, 'sound' => true];

    /**
     * @param array<string,mixed> $overrides Text and approved href values only.
     */
    public static function render(
        string $trustedTemplate,
        string $schemaJson,
        array $overrides
    ): string {
        $schema = json_decode($schemaJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($schema) || ($schema['version'] ?? null) !== 1) {
            throw new RuntimeException('Invalid v10 content registry');
        }
        $allowed = [];
        foreach (['text_fields', 'link_fields'] as $bucket) {
            if (!is_array($schema[$bucket] ?? null)) {
                throw new RuntimeException('Missing typed content fields');
            }
            foreach ($schema[$bucket] as $field) {
                if (!is_array($field) ||
                    !is_string($field['key'] ?? null) ||
                    !is_string($field['section'] ?? null)) {
                    throw new RuntimeException('Invalid editorial field');
                }
                if (isset(self::SECTIONS[$field['section']])) {
                    $allowed[$field['key']] = true;
                }
            }
        }

        foreach ($overrides as $key => $value) {
            if (!is_string($key) || !isset($allowed[$key])) {
                throw new InvalidArgumentException('Field outside first-screen editor');
            }
            if (!is_string($value)) {
                throw new InvalidArgumentException('Only plain string edits are supported');
            }
        }

        return V10Renderer::render($trustedTemplate, $schemaJson, $overrides);
    }
}
