#!/bin/bash
# Sets up SpaceAge on a fresh Ubuntu 24.04 server (run as root from /opt/spaceage).
# Expects /etc/spaceage.env with IG_ACCESS_TOKEN and BFL_API_KEY.
set -euo pipefail
APP=/opt/spaceage

timedatectl set-timezone Europe/Berlin
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv caddy cron curl ffmpeg
python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install --quiet requests pillow numpy

id spaceage >/dev/null 2>&1 || useradd --system --home-dir /var/lib/spaceage --shell /usr/sbin/nologin spaceage
mkdir -p /var/lib/spaceage /srv/spaceage/www "$APP/spaceage/queue" "$APP/spaceage/posted"
touch /var/log/spaceage.log
chown -R spaceage: /var/lib/spaceage /srv/spaceage/www "$APP/spaceage/queue" "$APP/spaceage/posted" /var/log/spaceage.log
chmod +x "$APP/spaceage/server/run.sh"

# Public HTTPS address without an own domain: <ip>.sslip.io, certificate by Caddy
ip=$(curl -4 -fsS https://api.ipify.org)
host="${ip//./-}.sslip.io"
cat > /etc/caddy/Caddyfile <<CADDY
$host {
	root * /srv/spaceage/www
	file_server
}
CADDY
systemctl restart caddy
grep -q '^SPACEAGE_PUBLIC_URL=' /etc/spaceage.env || echo "SPACEAGE_PUBLIC_URL=https://$host" >> /etc/spaceage.env
chown root:spaceage /etc/spaceage.env
chmod 640 /etc/spaceage.env

# 4 posts a day (Berlin time)
cat > /etc/cron.d/spaceage <<CRON
7 9,13,17,21 * * * spaceage $APP/spaceage/server/run.sh >> /var/log/spaceage.log 2>&1
CRON

# First check: is the Instagram token ok? Result on https://$host/status.txt
sleep 20  # give Caddy time for the certificate
sudo -u spaceage "$APP/spaceage/server/run.sh" --check >> /var/log/spaceage.log 2>&1 || true
echo "SpaceAge ready: https://$host/status.txt"
