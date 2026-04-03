FROM php:8.3-cli-alpine
RUN apk add --no-cache postgresql-dev curl && docker-php-ext-install pdo pdo_pgsql
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
WORKDIR /app
COPY composer.json .
RUN composer install --no-dev --no-interaction --optimize-autoloader
COPY . .
EXPOSE 8087
CMD ["php", "-S", "0.0.0.0:8087", "-t", "public", "public/index.php"]
