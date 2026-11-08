<?php

declare(strict_types=1);

namespace Celikom\Admin;

/** Server-rendered second confirmation, deliberately independent of JavaScript. */
final class BulkModerationView
{
    private static function e(mixed $value): string
    {
        return htmlspecialchars((string)($value ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    }

    public static function confirmation(string $csrf, array $selected, array $rows, string $action): string
    {
        $count = count($selected);
        $label = match ($action) {
            'approve'=>'Одобрение','reject'=>'Отклонение','delete'=>'Удаление',
            default=>'Массовое решение'
        };
        $html = '<section class="panel bulk-confirm"><a href="/admin?tab=uploads&amp;status=pending&amp;per_page=50">← Назад к списку</a>'
            . '<h1>' . self::e($label) . ': ' . $count . ' версий</h1>'
            . '<p class="muted">Ещё ничего не изменилось. Проверьте каждую выбранную запись перед подтверждением.</p>'
            . '<ol class="bulk-review-list">';
        foreach ($rows as $r) {
            $display = trim((string)$r['artist'] . ' — ' . (string)$r['title']);
            $html .= '<li><strong>#' . (int)$r['id'] . ' · ' . self::e($display) . '</strong>'
                . '<span>Track ID ' . self::e($r['service_track_id']) . ' · '
                . self::e($r['status']) . '</span></li>';
        }
        $html .= '</ol><form method="post" action="/admin/bulk/execute" class="bulk-confirm-form">'
            . '<input type="hidden" name="csrf" value="' . self::e($csrf) . '">'
            . '<input type="hidden" name="bulk_action" value="' . self::e($action) . '">';
        foreach ($selected as $id => $state) {
            $html .= '<input type="hidden" name="selected[' . (int)$id . ']" value="'
                . (int)$state['version'] . ':' . (int)$state['active'] . '">';
        }
        if ($action === 'approve') {
            $html .= '<p>Одобрение активирует подмены. Проверка источника сама по себе не подтверждает права.</p>'
                . '<label class="rights-check"><input type="checkbox" name="rights_confirmed" value="1" required>'
                . 'Подтверждаю, что лично проверил выбранные записи, качество аудио и права на использование</label>';
        } elseif ($action === 'reject') {
            $html .= '<label class="form-field">Общая причина отклонения'
                . '<select class="reject-category" name="reject_category" required>'
                . '<option value="" selected disabled>Выберите причину</option>'
                . '<option value="duplicate">Дубликат</option>'
                . '<option value="wrong_track">Не тот трек</option>'
                . '<option value="bad_quality">Плохое качество</option>'
                . '<option value="rights">Проблемы с правами</option>'
                . '<option value="other">Другая причина</option></select></label>';
        } elseif ($action === 'delete') {
            $html .= '<p class="bulk-danger-note">Необратимое удаление. Записи с заявками, жалобами, наградами'
                . ' или другими ссылками будут защищены. Аудит и запрет автоматического повторного импорта сохраняются.</p>'
                . '<label class="form-field">Введите число ' . $count . ' для подтверждения'
                . '<input type="number" name="confirm_count" min="' . $count . '" max="' . $count
                . '" required autocomplete="off"></label>';
        }
        $html .= '<label class="form-field">Общий комментарий'
            . ($action === 'reject' ? ' (обязателен для «Другой причины»)' : ' (необязательно)')
            . '<textarea name="review_note" maxlength="180" rows="3"></textarea></label>'
            . '<label class="rights-check"><input type="checkbox" name="confirm_batch" value="1" required>'
            . 'Подтверждаю решение для ' . $count . ' выбранных записей</label>'
            . '<button class="' . ($action === 'approve' ? 'primary' : 'danger')
            . '" type="submit">Подтвердить: ' . self::e(mb_strtolower($label,'UTF-8'))
            . ' (' . $count . ')</button></form></section>';
        return $html;
    }

    public static function result(array $r): string
    {
        $html = '<section class="panel bulk-results"><h1>Результат массовой операции</h1>'
            . '<p><strong>Обработано: ' . count($r['success']) . '</strong> · '
            . 'Пропущено: ' . count($r['conflicts']) . '</p>'
            . '<p class="muted">Партия: <code>' . self::e($r['batch'])
            . '</code>. Каждое решение зафиксировано в журнале.</p>';
        if ($r['success']) $html .= '<p>Успешные ID: ' . implode(', ',array_map('intval',$r['success'])) . '</p>';
        if ($r['conflicts']) {
            $html .= '<h2>Пропущенные записи</h2><ul>';
            foreach ($r['conflicts'] as $id => $error)
                $html .= '<li>#' . (int)$id . ' · ' . self::e($error) . '</li>';
            $html .= '</ul><p>Обновите очередь и повторите только нужные записи.</p>';
        }
        if ($r['cleanup_warnings'])
            $html .= '<p class="bulk-danger-note">Проверьте очистку приватного хранилища для ID '
                . implode(', ',array_map('intval',$r['cleanup_warnings']))
                . ': удаление записи прошло, но файл мог остаться в хранилище.</p>';
        return $html . '<a class="btn" href="/admin?tab=uploads&amp;status=pending&amp;per_page=50">'
            . 'Обновить очередь</a></section>';
    }
}
