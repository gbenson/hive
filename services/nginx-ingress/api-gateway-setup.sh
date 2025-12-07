#!/bin/sh
for h in $(grep '^API_GATEWAY' /run/secrets/hostnames.env | sed 's/.*=//' | sort); do
  sed "s/@@HOSTNAME@@/$h/g" < /etc/nginx/snippets/api-gateway-server.conf > /etc/nginx/conf.d/hive-api-gateway-$h.conf
  echo " - $h"
done
