<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;

/**
 * Local Stage 7 composite editorial preview, never a public route or CMS.
 * Factual transparency notices and material FAQ promises are read-only until
 * the owner approves a reviewed policy change. The core FAQ editor is reused.
 */
final class TrustDraft
{
    // Existing approved FAQ content about availability, trial, money,
    // contribution rewards, upload rights and mobile status is locked in
    // this developer preview. Stage 9 requires explicit content review.
    private const PROTECTED_FAQ = [
        'faq-question-01' => true,
        'faq-question-02' => true,
        'faq-question-04' => true,
        'faq-question-05' => true,
        'faq-question-08' => true,
        'faq-question-09' => true,
        'faq-question-10' => true,
        'faq-question-11' => true,
        'faq-question-12' => true,
        'faq-question-13' => true,
        'faq-question-14' => true,
        'faq-question-15' => true,
        'faq-question-16' => true,
        'faq-question-17' => true,
        'faq-question-18' => true,
        'faq-question-21' => true,
        'faq-question-22' => true,
        'faq-question-25' => true,
    ];

    /**
     * @param array<string,mixed> $texts
     * @param array<string,mixed> $faqDraft
     */
    public static function render(
        string $trustedTemplate,
        string $schemaJson,
        string $faqSeedJson,
        array $texts = [],
        array $faqDraft = []
    ): string {
        $fields = TrustFieldCatalog::fields($schemaJson);
        foreach ($texts as $key => $value) {
            if (!is_string($key) || !isset($fields[$key]) || !is_string($value)) {
                throw new InvalidArgumentException('Field is outside Stage 7 scope');
            }
            TrustFieldCatalog::check($key, $value, $fields[$key]);
        }
        $updates = $faqDraft['updates'] ?? [];
        if (isset($faqDraft['updates']) && !is_array($updates)) {
            throw new InvalidArgumentException('Invalid FAQ updates');
        }
        foreach ($updates as $id => $_changes) {
            if (isset(self::PROTECTED_FAQ[$id])) {
                throw new InvalidArgumentException('Protected product/policy FAQ requires owner review');
            }
        }
        // Canonical v10 immutable template and FAQ seed are verified by their
        // dedicated renderers. No file write, payment, user uploads or network.
        $page = V10Renderer::render($trustedTemplate, $schemaJson, $texts);
        return FaqV10Renderer::render($page, $faqSeedJson, $faqDraft);
    }
}
