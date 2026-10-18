<?php
declare(strict_types=1);
namespace Celikom\Website;

/**
 * Additive owner-review polish layered AFTER v10 integrity verification and CMS
 * rendering. Source v10, content manifest and immutable published revisions
 * remain unchanged and continue to validate with their original hashes.
 */
final class CmsOwnerPolish
{
    public static function apply(string $html, ?string $publicDirectory = null): string
    {
        if (!str_contains($html, 'class="hero" id="top"')) {
            throw new \RuntimeException('Owner polish: unexpected approved site markup');
        }
        // A missing /media/celikom-popup-approved.png originally showed a broken
        // picture. Do not substitute an unrelated popup or pretend it is real UI.
        $hero = <<<'HTML'
<div class="visual owner-visual" aria-label="Фирменная иллюстрация CELIKOM">
  <div class="owner-art-orbit owner-art-orbit--outer" aria-hidden="true"></div>
  <div class="owner-art-orbit owner-art-orbit--inner" aria-hidden="true"></div>
  <div class="owner-art-core" aria-hidden="true"><img src="/assets/images/celikom-mark.svg" alt=""/></div>
  <div class="owner-art-wave owner-art-wave--one" aria-hidden="true"></div>
  <div class="owner-art-wave owner-art-wave--two" aria-hidden="true"></div>
  <div class="owner-art-wave owner-art-wave--three" aria-hidden="true"></div>
</div></div></section>
HTML;
        $pattern = '~<div aria-label="Фирменный графический фон[^"]*" class="visual">.*?</div></div></section>~su';
        $count = 0;
        $updated = preg_replace($pattern, $hero, $html, 1, $count);
        if (!is_string($updated) || $count !== 1) {
            throw new \RuntimeException('Owner polish: hero slot not found');
        }
        $html = $updated;
        $reward = <<<'HTML'
<div aria-hidden="true" class="reward-illustration owner-reward-illustration">
  <div class="owner-reward-glow"></div>
  <div class="owner-reward-badge"><img src="/assets/images/celikom-mark.svg" alt=""/></div>
  <div class="owner-reward-orbit owner-reward-orbit--one"></div>
  <div class="owner-reward-orbit owner-reward-orbit--two"></div>
</div>
HTML;
        $pattern = '~<div aria-hidden="true" class="reward-illustration">.*?</div>\s*</section>~su';
        $updated = preg_replace($pattern, $reward."\n</section>", $html, 1, $count);
        if (!is_string($updated) || $count !== 1) {
            throw new \RuntimeException('Owner polish: reward illustration missing');
        }
        $html = $updated;
        // The brand leads to the actual homepage, not an ambiguous #top.
        foreach (['brand','footer-brand'] as $class) {
            $pattern = '~(<a\s+[^>]*\bclass="'.preg_quote($class, '~').'"[^>]*\bhref=")[^"]*(")~u';
            $html = preg_replace($pattern, '$1/$2', $html, 1, $count);
            if (!is_string($html) || $count !== 1) {
                throw new \RuntimeException('Owner polish: homepage brand missing');
            }
        }
        $html = str_replace('aria-label="CELIKOM — наверх"', 'aria-label="CELIKOM — на главную"', $html);
        // There is no call to action in the closing statement: keep it editorial.
        $pattern = '~<a class="closing-link" href="#top">.*?</a>~su';
        $updated = preg_replace($pattern, '', $html, 1, $count);
        if (!is_string($updated) || $count !== 1) {
            throw new \RuntimeException('Owner polish: closing CTA missing');
        }
        $html = $updated;
        $css = '<link rel="stylesheet" href="/assets/css/v10/owner-polish.css"/>';
        $js = '<script src="/assets/js/v10/owner-polish.js" defer></script>';
        if (substr_count($html, '</head>') !== 1 || substr_count($html, '</body>') !== 1) {
            throw new \RuntimeException('Owner polish: invalid HTML envelope');
        }
        $html = str_replace('</head>', $css.'</head>', $html);
        $html = str_replace('</body>', $js.'</body>', $html);

        // Without the TWO *approved* comparison files we refuse to suggest a
        // playable real-song demo exists. The original switch remains a clearly
        // labeled visual diagram. This does not replace or imitate real audio.
        $audioReady = is_string($publicDirectory)
            && is_file($publicDirectory.'/assets/audio/demo-before.mp3')
            && is_file($publicDirectory.'/assets/audio/demo-after.mp3');
        if (!$audioReady) {
            $html = str_replace('class="demo-options" role="group">',
                'class="demo-options" role="group">', $html);
            $html = str_replace('<div class="demo-board-label">Схема звучания</div>',
                '<div class="demo-board-label">Схема звучания · аудиопример готовится</div>', $html);
        }
        return $html;
    }
}
