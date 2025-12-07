chown 0:0 /run/secrets
chmod 700 /run/secrets
self=$(basename $f)
for f in /run/secrets/*.htpasswd; do
  cat $f > /etc/nginx/$(basename $f)
done
for f in /run/secrets/*.env; do
  entrypoint_log "$self: Sourcing $f"
  . $f
  for v in $(sed 's/#.*//; /^[[:space:]]*$/d; s/^\([A-Z][A-Z0-9_]*[A-Z0-9]\)=.*/\1/' $f); do
    echo $v | grep -q ^API_GATEWAY || export $v
  done
done
entrypoint_log "$self: Result:"
env | sort | sed "s/^/ - /"
