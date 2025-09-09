#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${APP_DIR:-/opt/osint-dashboard}"
PY_VER="${PY_VER:-3}"
USER_NAME="${SUDO_USER:-$USER}"
# 1) deps
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git curl
# Optional build deps if you add more libs later
sudo apt-get install -y build-essential
# 2) install app
sudo mkdir -p "$APP_DIR"
sudo rsync -a ./ "$APP_DIR/"
sudo chown -R "$USER_NAME":"$USER_NAME" "$APP_DIR"
# 3) venv
cd "$APP_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
# 4) streamlit config for headless service
mkdir -p "$APP_DIR/.streamlit"
cat > "$APP_DIR/.streamlit/config.toml" <<'EOF'
[server]
headless = true
enableCORS = false
enableXsrfProtection = true
port = 8501
address = "0.0.0.0"
EOF
echo "Install complete. To run now:"
echo "  cd $APP_DIR && source .venv/bin/activate && streamlit run app.py"
echo ""
echo "To enable as a service:"
echo "  sudo cp systemd/osint-dashboard.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload && sudo systemctl enable --now osint-dashboard"
