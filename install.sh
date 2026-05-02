#!/usr/bin/env bash
# SirenWatch PM — Erstinstallation auf Ubuntu 22.04 LXC
set -e

REPO="https://github.com/tjk-solutions-de/sirenwatch-pm.git"
DIR="/opt/sirenwatch-pm"
SERVICE="sirenwatch-pm"

echo "=== SirenWatch PM — Installation ==="

# Abhängigkeiten
apt update -qq
apt install -y python3 python3-pip git

# Repo klonen oder updaten
if [ -d "$DIR/.git" ]; then
    echo "▶ Update..."
    git -C "$DIR" pull
else
    echo "▶ Klone Repo..."
    git clone "$REPO" "$DIR"
fi

# Python-Pakete
pip3 install -q -r "$DIR/requirements.txt"

# Passwort setzen (interaktiv wenn nicht gesetzt)
if [ -z "$PM_PASSWORD" ]; then
    read -rsp "PM Passwort: " PM_PASSWORD
    echo
fi

# Systemd-Service installieren
cp "$DIR/systemd/sirenwatch-pm.service" /etc/systemd/system/
# Passwort in Override schreiben
mkdir -p /etc/systemd/system/sirenwatch-pm.service.d
cat > /etc/systemd/system/sirenwatch-pm.service.d/password.conf << EOF
[Service]
Environment=PM_PASSWORD=${PM_PASSWORD}
WorkingDirectory=${DIR}
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE"
systemctl status "$SERVICE" --no-pager

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "✅ Fertig! SirenWatch PM läuft auf: http://${IP}:8083"
