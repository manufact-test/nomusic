<?php

declare(strict_types=1);

return [
    'environment' => getenv('CELIKOM_APP_ENV') ?: 'local',
    'debug' => filter_var(getenv('CELIKOM_APP_DEBUG') ?: '0', FILTER_VALIDATE_BOOL),
    'version' => getenv('CELIKOM_SERVICE_VERSION') ?: '0.1.0',
];
