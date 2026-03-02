FROM php:8.1-apache

# Enable apache rewrite (common for older apps)
RUN a2enmod rewrite

# Setup application directory
COPY app /var/www/html/
RUN chown -R www-data:www-data /var/www/html
RUN chmod -R 755 /var/www/html

# Block direct HTTP access to the internal directory via Apache config
RUN echo "<Directory /var/www/html/internal>" > /etc/apache2/conf-available/internal-block.conf && \
    echo "    Require all denied" >> /etc/apache2/conf-available/internal-block.conf && \
    echo "</Directory>" >> /etc/apache2/conf-available/internal-block.conf && \
    a2enconf internal-block

# Expose port and start apache
EXPOSE 80

# FLAG env var injected by whale; write flag at runtime then start Apache
CMD ["sh", "-c", \
     "echo \"CHC{0ld_8ut_g0ld_n3v3r_d13s_${FLAG}}\" > /var/www/html/internal/flag && \
      exec apache2-foreground"]
