# Безопасный деплой на VPS с VPN

Этот бот безопасно работает на одном сервере с VPN благодаря изоляции через Docker.

## Меры безопасности

### 1. Изоляция через Docker Network
- Бот и БД работают в изолированной Docker сети `nutrition_network`
- База данных **не пробрасывает** порты наружу (только `expose`, не `ports`)
- БД доступна только внутри Docker сети для контейнера бота

### 2. Отсутствие внешних портов
- Бот работает через Telegram API (исходящие соединения)
- Никакие порты не открываются на хосте
- VPN и бот не конфликтуют - у них нет общих портов

### 3. Переменные окружения
- Все секреты в `.env` файле (не коммитится в git)
- `.env` должен иметь права `600` (только владелец читает)

### 4. Изоляция файловой системы
- Данные БД в Docker volume (не на хосте)
- Контейнеры имеют минимальные права

## Установка на VPS

```bash
# 1. Создай директорию проекта
mkdir -p ~/nutrition_bot
cd ~/nutrition_bot

# 2. Скопируй файлы проекта на сервер
# (используй git clone, scp, или rsync)

# 3. Создай .env файл
nano .env
```

Содержимое `.env`:
```env
TELEGRAM_BOT_TOKEN=8798586544:AAHuO1HszeWg67HjvVlBgvsvSFjxYkTvMgM
TOKENCLUB_API_KEY=tc_live_619e1f6584d08e776c5b6c416ceac610e778cb0277d2cc3a
DATABASE_URL=postgresql+asyncpg://nutrition_user:ТВОЙ_НАДЕЖНЫЙ_ПАРОЛЬ@db:5432/nutrition_db
DB_PASSWORD=ТВОЙ_НАДЕЖНЫЙ_ПАРОЛЬ
DEBUG=False
LOG_LEVEL=INFO
```

```bash
# 4. Установи безопасные права на .env
chmod 600 .env

# 5. Запусти бота
docker-compose up -d

# 6. Проверь что все работает
docker-compose ps
docker-compose logs -f bot

# 7. Проверь что порты не открыты
sudo netstat -tulpn | grep docker
# Должны быть только порты VPN, никаких 5432 или других портов бота
```

## Проверка изоляции

```bash
# Проверь что БД недоступна снаружи
telnet localhost 5432
# Должна быть ошибка подключения

# Проверь Docker сети
docker network inspect nutrition_bot_nutrition_network
# Должны быть видны только контейнеры bot и db

# Проверь открытые порты на сервере
sudo ss -tulpn
# Не должно быть портов от бота (только VPN порты)
```

## Дополнительная защита (опционально)

### 1. Firewall правила
```bash
# Разреши только необходимые порты
sudo ufw status
sudo ufw allow ssh
sudo ufw allow <VPN_PORT>
sudo ufw enable

# Docker автоматически управляет своими правилами
```

### 2. Автоматические обновления
```bash
# Настрой unattended-upgrades для безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. Логирование
```bash
# Смотри логи бота регулярно
docker-compose logs -f bot

# Или настрой ротацию логов
docker-compose logs --tail=100 bot > bot.log
```

### 4. Бэкапы БД
```bash
# Создай бэкап
docker-compose exec db pg_dump -U nutrition_user nutrition_db > backup.sql

# Или настрой автоматический бэкап в cron
0 3 * * * cd ~/nutrition_bot && docker-compose exec -T db pg_dump -U nutrition_user nutrition_db > backups/backup_$(date +\%Y\%m\%d).sql
```

## Обновление бота

```bash
cd ~/nutrition_bot

# Останови контейнеры
docker-compose down

# Обнови код (git pull или скопируй новые файлы)

# Пересобери и запусти
docker-compose up -d --build

# Проверь логи
docker-compose logs -f bot
```

## Мониторинг

```bash
# Проверь статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Логи последних 100 строк
docker-compose logs --tail=100 bot

# Следи за логами в реальном времени
docker-compose logs -f bot
```

## Почему это безопасно с VPN на одном сервере?

1. **Разные сетевые пространства**: VPN и бот используют разные Docker сети или работают на разных сетевых интерфейсах
2. **Нет конфликтов портов**: Бот не слушает входящие порты, только исходящие соединения к Telegram
3. **Изолированная БД**: PostgreSQL доступна только внутри Docker сети, не на хосте
4. **Контейнеризация**: Даже если бот скомпрометируют, он изолирован от хоста и VPN
5. **Минимальная атака поверхность**: Нет открытых портов = нет точек входа для атак

VPN будет продолжать работать независимо от бота, и наоборот.
