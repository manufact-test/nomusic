<?php

declare(strict_types=1);

namespace Celikom\Application;

/** Derived queue progress preserves original proposals and moderation history. */
final class TrackRequestProgress
{
    public static function sql(): string
    {
        // Fixed alias and SQL only; no caller or request values interpolated.
        $match = "FROM tracks t JOIN track_replacements v ON v.track_id=t.id
            WHERE t.service=r.service AND t.service_track_id=r.service_track_id";
        return "CASE WHEN r.status='rejected' THEN 'rejected'
            WHEN EXISTS (SELECT 1 $match AND v.status='approved' AND v.is_active=1
                AND v.disabled_at IS NULL) THEN 'fulfilled'
            WHEN EXISTS (SELECT 1 $match AND v.status='pending' AND v.disabled_at IS NULL)
                THEN 'uploaded'
            ELSE r.status END";
    }
}
