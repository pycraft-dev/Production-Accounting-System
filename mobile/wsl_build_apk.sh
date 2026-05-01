#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! python3 -c 'import socket; socket.gethostbyname("pypi.org")' 2>/dev/null; then
  echo ""
  echo "ОШИБКА: в WSL не работает DNS (pypi.org не резолвится)."
  echo "Это типично для WSL2 при VPN, «хост»-файрволе или битом /etc/resolv.conf."
  echo ""
  echo "Сделайте:"
  echo "  1) В Ubuntu перейдите в эту папку (mobile) и выполните:  bash wsl_fix_dns.sh"
  echo "  2) В PowerShell:  wsl --shutdown"
  echo "  3) Снова: build_android_apk.bat  (или ./wsl_build_apk.sh)"
  echo "Подробнее: docs/DEPLOY_LOCAL.md — раздел «WSL: DNS и сборка APK»."
  echo ""
  exit 1
fi

VENV="${BUILDOZER_VENV:-$(pwd)/.buildozer_venv}"
if [[ ! -f "$VENV/bin/activate" ]]; then
  echo ">>> create venv: $VENV"
  python3 -m venv "$VENV"
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"
echo ">>> pip: buildozer"
pip install -q buildozer
echo ">>> buildozer android debug"
buildozer android debug
echo ">>> APK (если успех): $(pwd)/bin/"
ls -la bin/*.apk 2>/dev/null || true
