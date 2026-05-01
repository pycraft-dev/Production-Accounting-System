# Локальный сервер на вашем ПК

Рабочий каталог при командах API — **`backend/`** (см. корневой README).

## Быстрый старт

1. Установите зависимости и настройте `.env` (БД, `JWT_SECRET_KEY`).
2. Создайте администратора: `python scripts/create_first_admin.py` или полный сид `python scripts/seed_data.py`.
3. Запустите сервер для доступа из сети:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   Либо из корня репозитория: **`launcher.bat`** (кнопки: API, клиенты, `/docs`) или **`start_server.bat`** (только uvicorn).

## Брандмауэр Windows

Разрешите входящие TCP на порт (пример для 8000), от имени администратора:

```bat
netsh advfirewall firewall add rule name="PAS FastAPI" dir=in action=allow protocol=TCP localport=8000
```

## Локальный IP

```bat
ipconfig
```

Используйте IPv4 вида `192.168.x.x`. В десктопе и мобильном клиенте укажите базовый URL: `http://192.168.x.x:8000` (поле/переменная окружения, см. конфиг клиентов).

## Документация API

Откройте в браузере: `http://<ваш-ip>:8000/docs`.

## Публичный доступ

Кратко: туннель **ngrok** или **Cloudflare Tunnel** к `localhost:8000`; для постоянной работы удобнее VPS (Render и т.д.). Подробности — в `docs/NETWORK_SETUP.md`.

## WSL: DNS и сборка APK

Если при `build_android_apk.bat` / `wsl_build_apk.sh` появляется **`Temporary failure in name resolution`** при установке buildozer через pip, в WSL не настроен DNS.

1. Откройте **Ubuntu** (WSL).
2. Перейдите в каталог **`mobile`** проекта (тот же репозиторий, что в Windows).
3. Выполните: `bash wsl_fix_dns.sh` (понадобится пароль sudo).
4. Закройте WSL, в **PowerShell** выполните: `wsl --shutdown`.
5. Снова откройте Ubuntu и проверьте: `ping -c1 pypi.org`.
6. Запустите **`build_android_apk.bat`** из корня репозитория.

Если после скрипта **pypi.org** всё ещё не пингуется: отключите **VPN** на время сборки; в корпоративной сети с прокси может понадобиться настройка прокси для `pip`/`buildozer` отдельно. Скрипт подставляет в начало списка DNS **IP шлюза по умолчанию** (хост Windows) — часто именно так WSL получает рабочие имена.

### Режим «mirrored» (только часть сборок **Windows 11**)

На **Windows 10** (в т.ч. 22H2 / сборка **19045**) пункт **`networkingMode=mirrored`** **не поддерживается** — WSL пишет, что откатывается к NAT. Это **не ошибка**: просто уберите из **`%USERPROFILE%\.wslconfig`** блок с `networkingMode=mirrored`, чтобы не было предупреждения, и настраивайте DNS вручную (ниже).

**Mirrored** имеет смысл только на поддерживаемых версиях **Windows 11** (см. документацию Microsoft «WSL Networking»). Там по шагам:

1. Файл **`%USERPROFILE%\.wslconfig`**
2. Блок:

   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

3. **`wsl --shutdown`** → снова проверка **`ping pypi.org`**

### Windows 10 + NAT: ручной DNS (основной способ)

1. В **cmd**: **`ipconfig /all`**
2. У адаптера, через который у вас в Windows открываются сайты, скопируйте все **DNS-серверы** (IP).
3. В Ubuntu (в `wsl_fix_dns.sh` уже стоит `generateResolvConf=false`):

   ```bash
   sudo tee /etc/resolv.conf <<'EOF'
   nameserver ПЕРВЫЙ_DNS_С_IPCONFIG
   nameserver ВТОРОЙ_DNS_ЕСЛИ_ЕСТЬ
   EOF
   ```

4. Проверка резолва **без `nslookup`** (в чистой Ubuntu его часто нет):

   ```bash
   getent hosts pypi.org
   ```

   или:

   ```bash
   python3 -c 'import socket; socket.setdefaulttimeout(5); print(socket.gethostbyname("pypi.org"))'
   ```

   Установить **`nslookup`** можно **после** того, как заработает сеть:  
   `sudo apt update && sudo apt install -y bind9-dnsutils`

   Тогда можно дополнительно: **`nslookup pypi.org`** и **`nslookup pypi.org 8.8.8.8`**.

   Если запрос **напрямую к 8.8.8.8** через `nslookup` работает, а обычный — нет — в **`/etc/resolv.conf`** в начале поставьте **`nameserver 8.8.8.8`** (и при необходимости **`8.8.4.4`**).

5. **`wsl --shutdown`**, снова Ubuntu: **`ping -c1 pypi.org`**

Отключите **VPN** на время проверки. Антивирус/фаервол иногда блокирует исходящий UDP/53 из WSL — временно проверьте с отключённым фильтром для теста.

### Если `getent` / Python всё равно дают Errno -3

1. Запустите в каталоге **`mobile`**:

   ```bash
   sed -i 's/\r$//' wsl_dns_hard_reset.sh
   bash wsl_dns_hard_reset.sh
   ```

2. В **PowerShell**: **`wsl --shutdown`**, снова откройте Ubuntu.
3. Сначала проверьте **маршрут**, не имя:

   ```bash
   ping -c1 8.8.8.8
   ```

   - **Не пингуется** — проблема не в DNS, а в сети WSL (часто **VPN**, **брандмауэр Windows**, антивирус). Отключите VPN, в «Брандмауэр Windows» временно разрешите для **Частная сеть** или добавьте правило для **vEthernet (WSL)**.
   - **Пингуется**, но **`getent hosts pypi.org`** пусто — внешний DNS (53) может резаться; откройте **`ipconfig /all`** в Windows и пропишите **те же `nameserver`**, что у вашего активного адаптера, в **`/etc/resolv.conf`**, снова **`wsl --shutdown`**.

### DNS вручную (кратко, как раньше)

1. В Windows: **`ipconfig /all`**
2. У активного Wi‑Fi/Ethernet найдите **DNS-серверы** (один или два IP).
3. В Ubuntu: **`sudo nano /etc/resolv.conf`** — оставьте только строки `nameserver <IP>` с этих адресов (или см. блок «Windows 10 + NAT» выше).
4. **`wsl --shutdown`**, снова проверка **`ping pypi.org`**.

Путь в WSL к каталогу сборки **этого** проекта (кавычки обязательны):  
`cd "/mnt/c/Users/GoLLu/проекты Curcor/Production Accounting System/mobile"`

## Сборка APK через GitHub Actions

Если локальный WSL без сети, можно собирать в облаке: в репозитории есть workflow **`.github/workflows/build-android-apk.yml`**.

1. Залейте проект на GitHub (ветка **`main`** или **`master`**).
2. В репозитории: **Actions** → **Build Android APK** → **Run workflow** (или пуш в `main`/`master` с изменениями в **`mobile/`**).
3. После завершения: тот же workflow-run → секция **Artifacts** → скачайте **`pas-mobile-debug-apk`** (внутри лежит `*.apk`).

Первый прогон долгий (скачивание SDK/NDK); повторные быстрее за счёт кэша **`.buildozer`**.