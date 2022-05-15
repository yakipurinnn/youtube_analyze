FROM php:8.1-apache

COPY php.ini-development /usr/local/etc/php/
COPY 000-default.conf /etc/apache2/sites-enabled/000-default.conf
COPY default-ssl.conf /etc/apache2/sites-enabled/default-ssl.conf

RUN cd /usr/bin && curl -s http://getcomposer.org/installer | php && ln -s /usr/bin/composer.phar /usr/bin/composer

# install Node.js
COPY --from=node:16.15 /usr/local/bin /usr/local/bin
COPY --from=node:16.15 /usr/local/lib /usr/local/lib

RUN apt-get update \
    && apt-get install -y libonig-dev git zip unzip vim libpng-dev libpq-dev&& \
    docker-php-ext-install pdo_mysql mysqli mbstring 

RUN mv /etc/apache2/mods-available/rewrite.load /etc/apache2/mods-enabled
RUN /bin/sh -c a2enmod rewrite

#ssl関係
# COPY ssl/server.crt /etc/ssl/certs/
# COPY ssl/server.key /etc/ssl/private/
COPY ssl/cert.pem /etc/ssl/certs/
COPY ssl/chain.pem /etc/ssl/certs/
COPY ssl/privkey.pem /etc/ssl/private/

RUN sed -i 's!/var/www/html!/var/www/html/laravelSample/public!g' /etc/apache2/sites-available/default-ssl.conf \
    && sed -i 's!/etc/ssl/certs/ssl-cert-snakeoil.pem!/etc/ssl/certs/server.crt!g' /etc/apache2/sites-available/default-ssl.conf \
    && sed -i 's!/etc/ssl/private/ssl-cert-snakeoil.key!/etc/ssl/private/server.key!g' /etc/apache2/sites-available/default-ssl.conf

RUN a2enmod ssl \
    # && a2ensite default-ssl.conf \
    && apache2ctl graceful