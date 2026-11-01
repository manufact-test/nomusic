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
        // Use the exact C path from the approved SVG, not its dark tile.
        // This remains sharp at every DPI and fits the existing pale orbit.
        $mark='<div class="familiar-orbit">'
            .'<svg class="celikom-familiar-c" aria-hidden="true" viewBox="0 0 128 128">'
            .'<path d="M92 40 A36 36 0 1 0 92 88"/></svg></div>';
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

        // v10 info icon's tiny implied dot was almost invisible at 20px.
        // Preserve the existing info circle and text but draw a real dot.
        $oldInfo='<div class="reward-notice"><svg aria-hidden="true" viewbox="0 0 24 24">'
            .'<circle cx="12" cy="12" r="9"></circle>'
            .'<path d="M12 11v5m0-8h.01"></path></svg>';
        $newInfo='<div class="reward-notice"><svg aria-hidden="true" viewbox="0 0 24 24">'
            .'<circle cx="12" cy="12" r="9"></circle>'
            .'<path d="M12 11v5"></path>'
            .'<circle class="celikom-info-dot" cx="12" cy="7.8" r="1.45"></circle></svg>';
        if (substr_count($html,$oldInfo)!==1) {
            throw new \RuntimeException('Approved information badge not found');
        }
        $html=str_replace($oldInfo,$newInfo,$html);

        // Owner-approved sound panel is enhanced after CMS render. Source v10
        // template, 11-section layout and original artwork remain untouched.
        $sourceLabel='<div class="demo-board-label">Схема звучания</div>';
        $soundLabel='<div class="demo-board-label">Рамиль — Ау</div>';
        if (substr_count($html,$sourceLabel)!==1) {
            throw new \RuntimeException('Original v10 sound label not found');
        }
        $html=str_replace($sourceLabel,$soundLabel,$html);
        $sourceFoot='<div><div aria-live="polite" class="demo-board-result" id="sound-result">Звучит версия из плеера</div><p class="demo-board-foot">Песни и плейлисты остаются в привычном сервисе.</p></div>';
        $clipDir=dirname(__DIR__,2).'/demo-audio/clips';
        // Never offer two independently labelled buttons backed by a
        // duplicated/incorrect demo source. The replacement's exact digest
        // comes from the separately cropped, verified live CELIKOM asset.
        $service=$clipDir.'/service.mp3';
        $restored=$clipDir.'/restored.mp3';
        $restoredDigest='d14e926aa506ec8ad3112cd73c516e935be1dca612e83dc46bca8c0f5a8342b5';
        $ready=is_file($service) && !is_link($service) &&
            is_file($restored) && !is_link($restored) &&
            filesize($service)>1000 && filesize($restored)>1000 &&
            hash_file('sha256',$restored)===$restoredDigest &&
            hash_file('sha256',$service)!==$restoredDigest;
        $readyValue=$ready?'true':'false';
        $playDisabled=$ready?'':' disabled';
        $newFoot='<div class="celikom-audio-controls">'
            .'<div class="celikom-audio-row">'
            .'<button type="button" class="celikom-audio-play" id="celikom-demo-play" '
            .'aria-label="Воспроизвести фрагмент" aria-pressed="false"'.$playDisabled.'>▶</button>'
            .'<div class="celikom-audio-timeline"><label class="celikom-visually-hidden" '
            .'for="celikom-demo-seek">Позиция воспроизведения</label>'
            .'<input type="range" id="celikom-demo-seek" min="0" max="11" '
            .'value="0" step="0.05" aria-label="Позиция воспроизведения" />'
            .'<span class="celikom-audio-time" id="celikom-demo-time">0:00 / 0:11</span></div>'
            .'</div><p class="celikom-audio-error" id="sound-result" aria-live="polite" hidden></p>'
            .'<audio id="celikom-demo-service" preload="none" src="/?demo_audio=service"></audio>'
            .'<audio id="celikom-demo-restored" preload="none" src="/?demo_audio=restored"></audio>'
            .'</div>';
        if (substr_count($html,$sourceFoot)!==1) {
            throw new \RuntimeException('Original v10 sound panel footer not found');
        }
        $html=str_replace($sourceFoot,$newFoot,$html);
        $html=str_replace('class="demo-board" data-mode="service" id="sound-panel"',
            'class="demo-board" data-mode="service" data-demo-ready="'.$readyValue.
            '" data-playing="false" id="sound-panel"',$html);
        $html=str_replace('aria-label="Визуальная схема принципа замены звука"',
            'aria-label="Сравнение звучания Ау"',$html);
        $oldDemoScript='<script src="/assets/js/v10/sound-demo.js"></script>';
        if (substr_count($html,$oldDemoScript)!==1) {
            throw new \RuntimeException('Source sound script not found');
        }
        $html=str_replace($oldDemoScript,
            '<script defer src="/assets/js/v10/owner-sound-player.js?v=511"></script>',$html);

        // Never expose the screenshot as an unprotected static file.
        // The exact uploaded original SHA is served by the protected home route.
        $html=str_replace('src="/media/celikom-popup-approved.png"',
            'src="/?v10_popup=approved"',$html);
        $css='<link rel="stylesheet" href="/assets/css/v10/owner-v10-motion.css?v=514"/>';
        $js='<script defer src="/assets/js/v10/owner-v10-motion.js?v=514"></script>';
        if (str_contains($html,$css)||str_contains($html,$js)) {
            throw new \RuntimeException('Duplicate owner motion assets');
        }
        return str_replace('</body>',$js.'</body>',
            str_replace('</head>',$css.'</head>',$html));
    }
}
