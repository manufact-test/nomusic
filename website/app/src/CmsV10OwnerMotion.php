<?php
declare(strict_types=1);
namespace Celikom\Website;

/**
 * Owner-reviewed v10 interaction layer, applied AFTER authenticated CMS render.
 *
 * Never edit the approved template, its manifest, published DB revisions,
 * illustrations, media choices, FAQ records, section structure or spacing.
 */
final class CmsV10OwnerMotion
{
    public static function apply(string $html): string
    {
        if (substr_count($html,'</head>') !== 1 ||
            substr_count($html,'</body>') !== 1 ||
            !str_contains($html,'id="sound"') ||
            !str_contains($html,'id="faq"') ||
            !str_contains($html,'id="closing"')) {
            throw new \RuntimeException('Unexpected CELIKOM v10 rendered markup');
        }
        // Both logo anchors navigate to the homepage, never "#top".
        foreach (['brand','footer-brand'] as $name) {
            $pattern='~(<a[^>]+class="'.preg_quote($name,'~').'"[^>]*href=")[^"]*(")~u';
            $count=0;
            $next=preg_replace($pattern,'$1/$2',$html,1,$count);
            if (!is_string($next)||$count!==1) {
                throw new \RuntimeException('v10 brand link not found: '.$name);
            }
            $html=$next;
        }
        $html=str_replace('aria-label="CELIKOM — наверх"',
            'aria-label="CELIKOM — на главную"',$html);

        // Owner accepted the closing visual but rejected the "Наверх" CTA.
        $count=0;
        $next=preg_replace('~<a class="closing-link" href="[^"]*">.*?</a>~su',
            '',$html,1,$count);
        if (!is_string($next)||$count!==1) {
            throw new \RuntimeException('v10 closing CTA not found');
        }
        $html=$next;

        // Three distinct header destinations, preserving existing header grid,
        // and the compact installation CTA on narrow widths.
        $navPattern='~<nav aria-label="Навигация">.*?</nav><a class="header-chip" href="#how">.*?</a>~us';
        $newNav='<nav aria-label="Навигация">'
            .'<a href="#contribute">Участие</a>'
            .'<a href="#faq">Вопросы</a>'
            .'</nav><a class="header-chip" href="#install">Установка →</a>';
        $count=0;
        $next=preg_replace($navPattern,$newNav,$html,1,$count);
        if (!is_string($next)||$count!==1) {
            throw new \RuntimeException('Approved header navigation not found');
        }
        $html=$next;

        // Replace only the confusing Z-like waveform inside the familiar-player
        // circle with the existing CELIKOM C mark. No artwork redraw.
        $wave='<div class="familiar-orbit"><svg aria-hidden="true" viewbox="0 0 24 24">'
            .'<path d="M2 12c3.5 0 3.5-8 7-8s3.5 16 7 16 3.5-8 6-8"></path></svg></div>';
        $mark='<div class="familiar-orbit">'
            .'<img src="/assets/images/celikom-mark.svg" alt=""/></div>';
        if (substr_count($html,$wave)!==1) {
            throw new \RuntimeException('Approved familiar-player icon not found');
        }
        $html=str_replace($wave,$mark,$html);

        // The approved image box stays the same size/shape; the oval outline
        // around its checkmark becomes a mathematically circular SVG path.
        $oval='<div class="reward-symbol"><svg viewbox="0 0 64 64">'
            .'<path d="M24 21c-7 0-11 5-11 11 0 6 5 11 11 11h16c7 0 11-5 11-11 0-6-5-11-11-11H24Z"></path>'
            .'<path d="m27 33 5 5 9-12"></path></svg></div>';
        $circle='<div class="reward-symbol"><svg viewbox="0 0 64 64">'
            .'<circle cx="32" cy="32" r="21"></circle>'
            .'<path d="m22 32 7 7 14-15"></path></svg></div>';
        if (substr_count($html,$oval)!==1) {
            throw new \RuntimeException('Approved reward checkmark missing');
        }
        $html=str_replace($oval,$circle,$html);

        // Never expose the screenshot as an unprotected static file.
        // The exact uploaded original SHA is served by the protected home route.
        $html=str_replace('src="/media/celikom-popup-approved.png"',
            'src="/?v10_popup=approved"',$html);
        $css='<link rel="stylesheet" href="/assets/css/v10/owner-v10-motion.css"/>';
        $js='<script defer src="/assets/js/v10/owner-v10-motion.js"></script>';
        if (str_contains($html,$css)||str_contains($html,$js)) {
            throw new \RuntimeException('Duplicate owner motion assets');
        }
        return str_replace('</body>',$js.'</body>',
            str_replace('</head>',$css.'</head>',$html));
    }
}
