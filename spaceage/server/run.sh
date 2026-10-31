#!/bin/bash
# One posting round with the settings from /etc/spaceage.env
set -a
. /etc/spaceage.env
set +a
exec /opt/spaceage/venv/bin/python /opt/spaceage/spaceage/server/run.py "$@"
