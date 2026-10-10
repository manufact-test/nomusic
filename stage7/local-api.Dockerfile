FROM php:8.3-apache

RUN docker-php-ext-install pdo_mysql \
    && a2enmod rewrite \
    && sed -i 's!/var/www/html!/var/www/celikom/public!g' /etc/apache2/sites-available/000-default.conf \
    && printf '<Directory /var/www/celikom/public>\nAllowOverride All\nRequire all granted\n</Directory>\n' > /etc/apache2/conf-available/celikom-local.conf \
    && a2enconf celikom-local \
    && printf 'upload_max_filesize=32M\npost_max_size=34M\nmax_execution_time=120\nmemory_limit=128M\ndisplay_errors=0\n' > /usr/local/etc/php/conf.d/celikom-upload.ini \
    && mkdir -p /var/private/audio \
    && chown -R www-data:www-data /var/private

COPY --chown=www-data:www-data . /var/www/celikom
WORKDIR /var/www/celikom
EXPOSE 80
