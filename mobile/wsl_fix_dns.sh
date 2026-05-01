#!/usr/bin/env bash
# Фикс DNS в WSL2, если pip: "Temporary failure in name resolution".
# Запуск в Ubuntu из каталога mobile:  sed -i 's/\r$//' wsl_fix_dns.sh && bash wsl_fix_dns.sh
# Затем в PowerShell:  wsl --shutdown

set -euo pipefail

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Запустите без sudo:  bash wsl_fix_dns.sh"
  exit 1
fi

WIN_NS=$(ip route show default 2>/dev/null | awk '{print $3; exit}')
echo "Настраиваю DNS (sudo). Шлюз Windows (если есть): ${WIN_NS:-нет}"
echo "Настраиваю /etc/wsl.conf и /etc/resolv.conf ..."

sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[network]
generateResolvConf = false
EOF

if [[ -L /etc/resolv.conf ]] || [[ -f /etc/resolv.conf ]]; then
  sudo rm -f /etc/resolv.conf
fi

{
  echo "# wsl_fix_dns.sh — generateResolvConf=false в /etc/wsl.conf"
  if [[ -n "${WIN_NS:-}" ]]; then
    echo "nameserver ${WIN_NS}"
  fi
  echo "nameserver 8.8.8.8"
  echo "nameserver 8.8.4.4"
  echo "nameserver 1.1.1.1"
} | sudo tee /etc/resolv.conf > /dev/null
sudo chmod 644 /etc/resolv.conf

echo ""
echo "Проверка резолва pypi.org (до ~8 с, не зависнет)..."
if python3 -c 'import socket; socket.setdefaulttimeout(8); socket.gethostbyname("pypi.org")' 2>/dev/null; then
  echo "  OK: pypi.org резолвится."
else
  echo "  ВНИМАНИЕ: за 8 с имя не разрешилось (или сеть/VPN режет DNS)."
  echo "  Файлы /etc/wsl.conf и /etc/resolv.conf уже записаны — сделайте wsl --shutdown и проверьте снова."
  echo "  Отключите VPN на время сборки."
  echo "  Windows 11: файл ~/.wslconfig в Windows (см. docs/DEPLOY_LOCAL.md) — networkingMode=mirrored"
  echo "  Или пропишите в /etc/resolv.conf те же DNS, что в ipconfig /all"
fi

echo ""
echo "Дальше:"
echo "  1) Закройте все окна Ubuntu/WSL."
echo "  2) PowerShell:  wsl --shutdown"
echo "  3) Новый Ubuntu:  ping -c1 pypi.org"
echo "  4) build_android_apk.bat"
echo ""
