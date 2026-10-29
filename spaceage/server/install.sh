#!/bin/bash
# Sets up SpaceAge on a fresh Ubuntu 24.04 server (run as root from /opt/spaceage).
# Expects /etc/spaceage.env with IG_ACCESS_TOKEN and BFL_API_KEY.
set -euo pipefail
APP=/opt/spaceage

timedatectl set-timezone Europe/Berlin
# 2 GB swap as a safety net: building a reel needs ~0.6 GB for ffmpeg
if [ ! -f /swapfile ]; then
	fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
	echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi
# wait for the first-boot automatic updates instead of failing on the dpkg lock
apt-get -o DPkg::Lock::Timeout=900 update
DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=900 install -y python3-venv caddy cron curl ffmpeg
python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install --quiet requests pillow numpy anthropic

id spaceage >/dev/null 2>&1 || useradd --system --home-dir /var/lib/spaceage --shell /usr/sbin/nologin spaceage
mkdir -p /var/lib/spaceage /srv/spaceage/www "$APP/spaceage/queue" "$APP/spaceage/posted"
touch /var/log/spaceage.log
chown -R spaceage: /var/lib/spaceage /srv/spaceage/www "$APP/spaceage/queue" "$APP/spaceage/posted" /var/log/spaceage.log
chmod +x "$APP/spaceage/server/run.sh"

# Public HTTPS address without an own domain: <ip>.sslip.io, certificate by Caddy
ip=$(curl -4 -fsS https://api.ipify.org)
host="${ip//./-}.sslip.io"
# Upload page for own images: https://$host/upload, user "spaceage" + password
pwfile=/root/spaceage-upload-passwort.txt
if [ ! -s "$pwfile" ]; then  # (tr | head would die of SIGPIPE under pipefail)
	python3 -c "import secrets; print(''.join(secrets.choice('abcdefghjkmnpqrstuvwxyz23456789') for _ in range(12)), end='')" > "$pwfile"
fi
chmod 600 "$pwfile"
pwhash=$(caddy hash-password --plaintext "$(cat "$pwfile")")
cat > /etc/caddy/Caddyfile <<CADDY
$host {
	handle /upload* {
		basicauth {
			spaceage $pwhash
		}
		reverse_proxy 127.0.0.1:8081
	}
	handle {
		root * /srv/spaceage/www
		file_server
	}
}
CADDY
cat > /etc/systemd/system/spaceage-upload.service <<UNIT
[Unit]
Description=SpaceAge upload page
After=network.target

[Service]
User=spaceage
ExecStart=$APP/venv/bin/python $APP/spaceage/server/upload.py
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable spaceage-upload
systemctl restart spaceage-upload
systemctl restart caddy
grep -q '^SPACEAGE_PUBLIC_URL=' /etc/spaceage.env || echo "SPACEAGE_PUBLIC_URL=https://$host" >> /etc/spaceage.env
chown root:spaceage /etc/spaceage.env
chmod 640 /etc/spaceage.env

# a post every four hours (Berlin time): 8:07, 12:07, 16:07, 20:07
cat > /etc/cron.d/spaceage <<CRON
7 8,12,16,20 * * * spaceage $APP/spaceage/server/run.sh >> /var/log/spaceage.log 2>&1
CRON

# First check: is the Instagram token ok? Result on https://$host/status.txt
sleep 20  # give Caddy time for the certificate
runuser -u spaceage -- "$APP/spaceage/server/run.sh" --check >> /var/log/spaceage.log 2>&1 || true
echo "FERTIG: https://$host/status.txt - Uploads: https://$host/upload"
# setup log page on port 8080 is no longer needed
systemctl stop spaceage-setup || true
