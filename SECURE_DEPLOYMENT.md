# Безопасная установка с отдельным пользователем

## Почему отдельный пользователь важен:

1. **Изоляция от VPN** - если что-то пойдет не так с ботом, VPN останется защищенным
2. **Минимальные привилегии** - бот работает под непривилегированным пользователем
3. **Разделение ответственности** - VPN управляется одним юзером, бот - другим
4. **Аудит** - легко отследить кто что делал в системе

## Установка с нуля

### Шаг 1: Создай отдельного пользователя на VPS

```bash
# Подключись к VPS под root или sudo пользователем
ssh your-main-user@your-vps

# Создай пользователя для бота
sudo adduser nutritionbot

# Добавь в группу docker (чтобы мог запускать контейнеры)
sudo usermod -aG docker nutritionbot

# Проверь что пользователь создан
id nutritionbot
```

### Шаг 2: Переключись на нового пользователя

```bash
# Переключись на пользователя бота
sudo su - nutritionbot

# Проверь что ты под правильным пользователем
whoami
# Должно вывести: nutritionbot

pwd
# Должно вывести: /home/nutritionbot
```

### Шаг 3: Установи проект

```bash
# Создай директорию для бота
mkdir -p ~/nutrition_bot
cd ~/nutrition_bot

# Скопируй файлы проекта (из основного пользователя или через git)
# Вариант 1: Через git
git clone <your-repo> .

# Вариант 2: Скопировать из другой директории (если файлы уже на сервере)
# sudo cp -r /path/to/nutrition_bot/* /home/nutritionbot/nutrition_bot/
# sudo chown -R nutritionbot:nutritionbot /home/nutritionbot/nutrition_bot
```

### Шаг 4: Настрой .env файл

```bash
cd ~/nutrition_bot

# Создай .env из примера
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=8798586544:AAHuO1HszeWg67HjvVlBgvsvSFjxYkTvMgM
TOKENCLUB_API_KEY=tc_live_619e1f6584d08e776c5b6c416ceac610e778cb0277d2cc3a
DATABASE_URL=postgresql+asyncpg://nutrition_user:ПРИДУМАЙ_СЛОЖНЫЙ_ПАРОЛЬ@db:5432/nutrition_db
DB_PASSWORD=ПРИДУМАЙ_СЛОЖНЫЙ_ПАРОЛЬ
DEBUG=False
LOG_LEVEL=INFO
EOF

# Отредактируй .env и поставь надежный пароль БД
nano .env

# Установи права только на чтение для владельца
chmod 600 .env

# Проверь что права правильные
ls -la .env
# Должно быть: -rw------- 1 nutritionbot nutritionbot
```

### Шаг 5: Запусти бота

```bash
cd ~/nutrition_bot

# Запусти в фоновом режиме
docker-compose up -d

# Проверь что контейнеры запустились
docker-compose ps

# Посмотри логи
docker-compose logs -f bot
```

### Шаг 6: Настрой автозапуск через systemd (опционально)

```bash
# Выйди из пользователя nutritionbot
exit

# Вернись под sudo пользователя и создай systemd сервис
sudo nano /etc/systemd/system/nutrition-bot.service
```

Содержимое файла сервиса:
```ini
[Unit]
Description=Nutrition Telegram Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=nutritionbot
Group=nutritionbot
WorkingDirectory=/home/nutritionbot/nutrition_bot
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Включи и запусти сервис
sudo systemctl daemon-reload
sudo systemctl enable nutrition-bot.service
sudo systemctl start nutrition-bot.service

# Проверь статус
sudo systemctl status nutrition-bot.service
```

## Проверка безопасности

```bash
# 1. Проверь что БД недоступна снаружи
telnet localhost 5432
# Должно быть: Connection refused

# 2. Проверь открытые порты
sudo ss -tulpn
# Не должно быть портов 5432 или других от бота

# 3. Проверь изоляцию пользователей
sudo ps aux | grep nutrition
# Процессы должны быть от пользователя nutritionbot

# 4. Проверь Docker сеть
sudo docker network inspect nutrition_bot_nutrition_network
# Только контейнеры bot и db

# 5. Проверь что пользователь nutritionbot не имеет sudo
sudo -l -U nutritionbot
# Должно вывести что нет sudo прав
```

## Управление ботом

```bash
# Переключись на пользователя бота
sudo su - nutritionbot
cd ~/nutrition_bot

# Посмотреть логи
docker-compose logs -f bot

# Перезапустить
docker-compose restart

# Остановить
docker-compose down

# Обновить и перезапустить
docker-compose down
git pull  # или скопируй новые файлы
docker-compose up -d --build

# Выйти из пользователя
exit
```

## Бэкапы БД

```bash
# Под пользователем nutritionbot
sudo su - nutritionbot
cd ~/nutrition_bot

# Создай директорию для бэкапов
mkdir -p ~/backups

# Сделай бэкап
docker-compose exec -T db pg_dump -U nutrition_user nutrition_db > ~/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Настрой автоматический бэкап в crontab
crontab -e

# Добавь строку (бэкап каждый день в 3:00)
0 3 * * * cd /home/nutritionbot/nutrition_bot && docker-compose exec -T db pg_dump -U nutrition_user nutrition_db > /home/nutritionbot/backups/backup_$(date +\%Y\%m\%d).sql

# Удаление старых бэкапов (старше 30 дней)
0 4 * * * find /home/nutritionbot/backups -name "backup_*.sql" -mtime +30 -delete
```

## Firewall (ufw)

```bash
# Под sudo пользователем
sudo ufw status

# Если VPN на определенных портах, убедись что они разрешены
# Например, WireGuard обычно на 51820
sudo ufw allow 51820/udp

# SSH должен быть разрешен
sudo ufw allow ssh

# Включи firewall если еще не включен
sudo ufw enable

# Проверь что нет лишних открытых портов
sudo ufw status numbered
```

## Мониторинг

```bash
# Добавь скрипт проверки здоровья бота
sudo su - nutritionbot
cat > ~/check_bot_health.sh << 'EOF'
#!/bin/bash
cd ~/nutrition_bot
if ! docker-compose ps | grep -q "Up"; then
    echo "Bot is down! Restarting..."
    docker-compose up -d
    echo "Bot restarted at $(date)" >> ~/bot_restarts.log
fi
EOF

chmod +x ~/check_bot_health.sh

# Добавь в crontab (проверка каждые 5 минут)
crontab -e
# Добавь:
*/5 * * * * /home/nutritionbot/check_bot_health.sh
```

## Итого: Почему это безопасно

✅ **Отдельный пользователь** - nutritionbot без sudo прав
✅ **Изоляция от VPN** - разные пользователи, разные процессы
✅ **Docker изоляция** - контейнеры в своей сети
✅ **Нет открытых портов** - только исходящие соединения
✅ **Файловая изоляция** - .env с правами 600
✅ **Минимальная атака поверхность** - нет лишних сервисов
✅ **Автоматические бэкапы** - данные защищены
✅ **Мониторинг** - автоперезапуск при падении

Даже если бот будет скомпрометирован (что крайне маловероятно), злоумышленник получит доступ только к изолированному пользователю nutritionbot без sudo прав, в Docker контейнере. VPN и остальная система останутся защищенными.
