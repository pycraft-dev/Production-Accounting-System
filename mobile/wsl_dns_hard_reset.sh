#!/usr/bin/env bash
# Жёстко выставить DNS в WSL (Google + Cloudflare), отключить автогенерацию resolv.conf.
# Запуск в Ubuntu:  sed -i 's/\r$//' wsl_dns_hard_reset.sh && bash wsl_dns_hard_reset.sh
# Затем обязательно в PowerShell Windows:  wsl --shutdown
# Снова Ubuntu:  ping -c1 8.8.8.8  и  getent hosts pypi.org

set -euo pipefail

echo "=== 1) Отключаем автогенерацию resolv.conf"
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[network]
generateResolvConf = false
EOF

echo "=== 2) Пишем /etc/resolv.conf"
sudo rm -f /etc/resolv.conf
sudo tee /etc/resolv.conf > /dev/null <<'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF
sudo chmod 644 /etc/resolv.conf

echo "=== 3) Содержимое /etc/resolv.conf:"
cat /etc/resolv.conf

echo ""
echo "=== 4) Сейчас (без перезапуска WSL) проверка может ещё не смениться."
echo "    Выполните в PowerShell:  wsl --shutdown"
echo "    Откройте Ubuntu снова, затем по порядку:"
echo "      ping -c1 8.8.8.8"
echo "      getent hosts pypi.org"
echo ""
echo "Если ping 8.8.8.8 НЕ идёт — у WSL нет выхода в интернет (VPN, фаервол, антивирус)."
echo "Если ping идёт, а pypi.org нет — провайдер/офис режет DNS; возьмите DNS из ipconfig /all в Windows"
echo "и замените строки nameserver в /etc/resolv.conf вручную: sudo nano /etc/resolv.conf"
echo ""
