<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;

/**
 * Stage 9 scoped CMS editorial composite. All sections share ONE immutable
 * v10 content manifest; protected product promises and visual markup remain
 * outside the owner's normal copy editor.
 *
 * Demo state adapter (sound.text.07 / sound.result.restored) is intentionally
 * excluded until cross-section JS adapter parity is separately reverified.
 */
final class CmsEditor
{
    /** @return array<string,array<string,mixed>> */
    public static function fields(string $manifest): array
    {
        $first = FirstScreenFieldCatalog::fields($manifest);
        unset($first[FirstScreenFieldCatalog::RESTORED_KEY], $first['sound.text.07']);
        $principle = PrincipleFieldCatalog::fields($manifest);
        $community = CommunityFieldCatalog::fields($manifest);
        $trust = TrustFieldCatalog::fields($manifest);
        $finish = InstallFooterFieldCatalog::fields($manifest);
        $all = [];
        foreach ([$first,$principle,$community,$trust,$finish['texts'],$finish['links'],CmsSeoCatalog::fields($manifest)] as $bucket) {
            foreach ($bucket as $key => $field) {
                if (isset($all[$key])) {
                    throw new \RuntimeException('Duplicate CMS catalog key');
                }
                $all[$key] = $field;
            }
        }
        return $all;
    }

    /**
     * Complete editor snapshot -> approved HTML. Called before each draft
     * save, preview, publication, rollback and public published read.
     *
     * @param array{content:array<string,string>,faq:array<string,mixed>} $data
     */
    public static function validate(
        string $template,
        string $manifest,
        string $faqSeed,
        array $data
    ): string {
        if (array_keys($data) !== ['content','faq'] ||
            !is_array($data['content']) || !is_array($data['faq']) ||
            (array_is_list($data['content']) && $data['content'] !== []) ||
            (array_is_list($data['faq']) && $data['faq'] !== [])) {
            throw new InvalidArgumentException('Unsupported editor snapshot');
        }
        $fields = self::fields($manifest);
        foreach ($data['content'] as $key=>$value) {
            if (!is_string($key) || !isset($fields[$key]) || !is_string($value)) {
                throw new InvalidArgumentException('Unapproved CMS field');
            }
            if (($fields[$key]['type']??null)==='metadata') {
                CmsSeoCatalog::check($key,$value,$fields[$key]);
            } elseif (str_starts_with($key,'header.') ||
                str_starts_with($key,'hero.') ||
                str_starts_with($key,'sound.')) {
                FirstScreenFieldCatalog::check($key,$value,$fields[$key]);
                if (($fields[$key]['type'] ?? null)==='url' &&
                    str_starts_with($value,'#') &&
                    substr_count($template, 'id="'.substr($value,1).'"') !== 1) {
                    throw new InvalidArgumentException('Header/Hero anchor target missing');
                }
            } elseif (str_starts_with($key,'features.') ||
                str_starts_with($key,'how.') ||
                str_starts_with($key,'player.')) {
                PrincipleFieldCatalog::check($key,$value,$fields[$key]);
            } elseif (str_starts_with($key,'contribute.') ||
                      str_starts_with($key,'rewards.')) {
                CommunityFieldCatalog::check($key,$value,$fields[$key]);
            } elseif (str_starts_with($key,'faq.') ||
                      str_starts_with($key,'transparency.')) {
                TrustFieldCatalog::check($key,$value,$fields[$key]);
            } elseif (($fields[$key]['type'] ?? null)==='anchor') {
                InstallFooterFieldCatalog::checkLink($key,$value,$fields[$key],$template);
            } else {
                InstallFooterFieldCatalog::checkText($key,$value,$fields[$key]);
            }
        }
        // FAQ protected originals need separate editorial review and cannot
        // be changed through this ordinary owner field editing route.
        if ($data['faq'] !== []) {
            TrustDraft::render($template,$manifest,$faqSeed,[],$data['faq']);
        }
        $page=V10Renderer::render($template,$manifest,$data['content']);
        $page=FaqV10Renderer::render($page,$faqSeed,$data['faq']);
        // The original v10 scripts/styles remain untouched; an additive
        // edited-copy stylesheet guards long header/hero text only.
        $firstEdited = array_filter(
            array_keys($data['content']),
            static fn(string $key): bool =>
                str_starts_with($key,'header.') || str_starts_with($key,'hero.')
        );
        if ($firstEdited !== []) {
            $css='<link rel="stylesheet" href="/assets/css/v10/editor-copy-safety.css"/>';
            if (substr_count($page,'</head>')!==1 || str_contains($page,$css)) {
                throw new \RuntimeException('Unexpected v10 preview head');
            }
            $page=str_replace('</head>',$css.'</head>',$page);
        }
        return $page;
    }
}
