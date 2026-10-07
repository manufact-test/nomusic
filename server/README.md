# CELIKOM server

Minimal PHP 8.3/Composer foundation for the future API. It deliberately contains no accounts, uploads, entitlements, billing or catalog business logic.

```bash
composer install
composer test
php -S 127.0.0.1:8080 -t public
```

Only `GET /health` is currently implemented. All unknown routes return JSON `404`.
