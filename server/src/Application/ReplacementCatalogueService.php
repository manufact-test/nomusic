<?php

declare(strict_types=1);

namespace Celikom\Application;

/**
 * Metadata-only snapshot of the currently approved Yandex replacements.
 * A snapshot is generated when requested. No audio, access tokens, storage
 * locations, uploader identities or unapproved submissions leave the server.
 */
final class ReplacementCatalogueService
{
    public const MAX_ROWS = 5000;

    public function __construct(private readonly \PDO $pdo)
    {
    }

    /** @return array<string, mixed> */
    public function snapshot(): array
    {
        $statement = $this->pdo->query("
            SELECT t.service_track_id AS track_id, t.title, t.artist, t.album,
                   t.duration_ms
              FROM tracks t
             WHERE t.service = 'yandex'
               AND EXISTS (
                   SELECT 1 FROM track_replacements r
                    WHERE r.track_id = t.id
                      AND r.status = 'approved'
                      AND r.is_active = 1
                      AND r.disabled_at IS NULL
               )
             ORDER BY t.id
             LIMIT " . (self::MAX_ROWS + 1));
        if ($statement === false) {
            throw new \RuntimeException('catalogue_query_failed');
        }

        $source = $statement->fetchAll(\PDO::FETCH_ASSOC);
        if (count($source) > self::MAX_ROWS) {
            // Never silently distribute a partial catalogue.
            throw new \RuntimeException('catalogue_limit_exceeded');
        }

        $items = [];
        $seen = [];
        foreach ($source as $row) {
            $id = (string) $row['track_id'];
            $title = trim((string) $row['title']);
            $artist = trim((string) $row['artist']);
            $duration = (int) $row['duration_ms'];
            if (!preg_match('/^[1-9][0-9]{0,19}$/D', $id)
                || $title === '' || $artist === ''
                || $duration < 1000 || $duration > 36000000
                || isset($seen[$id])) {
                throw new \RuntimeException('catalogue_invalid_row');
            }
            $seen[$id] = true;
            $items[] = [
                'track_id' => $id,
                'title' => $title,
                'artist' => $artist,
                'album' => (string) ($row['album'] ?? ''),
                'duration_ms' => $duration,
                'replacement_available' => true,
            ];
        }

        return [
            'schema' => 1,
            'source' => 'celikom_owner_catalog_snapshot',
            'generated_at_ms' => (int) round(microtime(true) * 1000),
            'complete' => true,
            'total_tracks' => count($items),
            'tracks' => $items,
        ];
    }
}
