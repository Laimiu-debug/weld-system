#!/bin/sh
set -eu

mkdir -p /etc/nginx/conf.d

if [ -s /etc/letsencrypt/live/sdhaohan.cn/fullchain.pem ] && \
   [ -s /etc/letsencrypt/live/sdhaohan.cn/privkey.pem ]; then
    cp /etc/nginx/weld-templates/default.conf /etc/nginx/conf.d/default.conf
    echo "weld nginx: using HTTPS configuration"
else
    cp /etc/nginx/weld-templates/default.conf.http /etc/nginx/conf.d/default.conf
    echo "weld nginx: certificate not found; using HTTP bootstrap configuration"
fi

# Certbot writes renewed certificates into the shared volume. Reload periodically
# so renewals take effect without restarting the stack.
(while sleep 12h; do nginx -s reload || true; done) &

exec /docker-entrypoint.sh nginx -g 'daemon off;'
