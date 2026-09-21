# Nutrition Bot для Telegram

Telegram бот для отслеживания КБЖУ (калории, белки, жиры, углеводы) и расчета профицита калорий.

## Возможности

- 📸 **Распознавание еды по фото** - отправьте фото блюда для автоматического подсчета КБЖУ
- 🏷 **Сканирование этикеток** - фото этикетки продукта для точных данных о питательной ценности
- ✍️ **Текстовый ввод** - опишите что съели текстом
- 📊 **Категоризация приемов пищи** - завтрак, обед, ужин, перекусы
- 🏃 **Учет расхода калорий** - интеграция с данными wearables (Whoop, Fitbit и др.)
- 📈 **Расчет профицита** - автоматический подсчет профицита/дефицита калорий
- ⚖️ **Логирование веса** - отслеживание изменений веса тела
- 📊 **Дневные сводки** - детальная статистика по приемам пищи и КБЖУ

## Технологии

- Python 3.11
- aiogram 3.x - фреймворк для Telegram ботов
- PostgreSQL - хранение данных
- SQLAlchemy 2.0 - ORM
- Token.club API - распознавание еды и парсинг текста
- Docker & Docker Compose - контейнеризация

## Установка и запуск

### Требования

- Docker и Docker Compose
- Telegram Bot Token (получить у [@BotFather](https://t.me/botfather))
- Token.club API Key (получить на [tooken.club](https://tooken.club))

### Настройка

1. Клонируйте репозиторий и перейдите в директорию:
```bash
cd nutrition_bot
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

3. Отредактируйте `.env` и укажите свои данные:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TOKENCLUB_API_KEY=your_tokenclub_api_key_here
DATABASE_URL=postgresql+asyncpg://nutrition_user:your_password@db:5432/nutrition_db
```

### Запуск через Docker

```bash
# Собрать и запустить
docker-compose up -d

# Посмотреть логи
docker-compose logs -f bot

# Остановить
docker-compose down
```

### Запуск без Docker (для разработки)

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить PostgreSQL и обновить DATABASE_URL в .env

# Запустить бота
python main.py
```

## Использование

### Команды

- `/start` - начать работу с ботом
- `/help` - справка по использованию
- `/stats` - сводка за сегодня
- `/burned <число>` - указать расход калорий (например: `/burned 2500`)
- `/weight <число>` - записать вес в кг (например: `/weight 75.5`)

### Добавление еды

**Способ 1: Фото еды**
- Отправьте фото блюда
- Бот распознает еду и подсчитает КБЖУ
- Выберите прием пищи (завтрак/обед/ужин/перекус)

**Способ 2: Фото этикетки**
- Отправьте фото этикетки с подписью "этикетка"
- Бот извлечет точные данные о питательной ценности
- Выберите прием пищи

**Способ 3: Текстовое описание**
- Напишите что съели: "2 яйца и тост с маслом"
- Бот распознает и подсчитает КБЖУ
- Выберите прием пищи

### Отслеживание профицита

1. Добавляйте приемы пищи в течение дня
2. Укажите расход калорий командой `/burned` (данные с wearables)
3. Используйте `/stats` чтобы увидеть:
   - Разбивку по приемам пищи
   - Общее потребление КБЖУ
   - Расход калорий
   - **Профицит или дефицит калорий**

## Структура проекта

```
nutrition_bot/
├── config.py                 # Конфигурация приложения
├── main.py                   # Точка входа
├── database/
│   ├── models.py            # SQLAlchemy модели
│   ├── connection.py        # Подключение к БД
│   └── repositories.py      # Репозитории для работы с БД
├── services/
│   ├── tokenclub_api.py     # Клиент Token.club API
│   ├── nutrition_parser.py  # Парсинг ответов API
│   └── statistics.py        # Подсчет статистики
├── handlers/
│   ├── basic.py             # /start, /help
│   ├── commands.py          # /stats, /burned, /weight
│   └── food_input.py        # Обработка фото и текста
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## API Token.club

Бот использует Token.club API для:
- **Vision API** (`https://tooken.club/v1/images/generations`) - распознавание еды на фото и OCR этикеток
- **Chat API** (`https://tooken.club/v1/chat/completions`) - парсинг текстовых описаний еды

Доступные модели для Chat API:
- `claude-opus-4-8` (рекомендуется для точности)
- `claude-opus-5`
- `claude-sonnet-5`
- `gpt-6-astra`
- `gpt-5.6-sol`

Для Vision API:
- `gpt-image-2` - используется для анализа фотографий еды

## Разработка

### Добавление новых функций

1. Модели данных: `database/models.py`
2. Репозитории: `database/repositories.py`
3. Обработчики: создайте новый router в `handlers/`
4. Зарегистрируйте router в `main.py`

### Изменение промптов для AI

Промпты для Token.club API находятся в:
- `services/tokenclub_api.py` - методы `analyze_food_image()`, `parse_text_food_description()`, `analyze_nutrition_label()`

### Тестирование

```bash
# TODO: Добавить юнит-тесты
pytest tests/
```

## Деплой на VPS

```bash
# На VPS
git clone <your-repo-url>
cd nutrition_bot
cp .env.example .env
nano .env  # Заполните переменные

# Запустить
docker-compose up -d

# Проверить логи
docker-compose logs -f
```

## Лицензия

MIT

## Автор

Создано для отслеживания профицита калорий при наборе массы 💪
