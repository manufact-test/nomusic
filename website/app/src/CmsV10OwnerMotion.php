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

        $css='<link rel="stylesheet" href="/assets/css/v10/owner-v10-motion.css"/>';
        $js='<script defer src="/assets/js/v10/owner-v10-motion.js"></script>';
        if (str_contains($html,$css)||str_contains($html,$js)) {
            throw new \RuntimeException('Duplicate owner motion assets');
        }
        return str_replace('</body>',$js.'</body>',
            str_replace('</head>',$css.'</head>',$html));
    }
}
