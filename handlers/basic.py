from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import async_session_maker, UserRepository

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

    welcome_text = """👋 Привет! Я помогу тебе отслеживать КБЖУ и профицит калорий.

<b>Что я умею:</b>
📸 Распознавать еду по фото
🏷 Считывать этикетки продуктов
✍️ Понимать текстовые описания еды
📊 Считать профицит калорий
⚖️ Логировать вес

<b>Как использовать:</b>
• Пришли фото еды или этикетки
• Напиши что съел текстом
• Используй команды ниже

<b>Команды:</b>
/stats - сводка за сегодня
/burned (число) - сколько калорий потратил
/weight (число) - записать вес в кг
/help - помощь"""

    await message.answer(welcome_text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """📚 <b>Справка по боту</b>

<b>Способы добавить еду:</b>

1️⃣ <b>Фото еды</b>
Просто пришли фото блюда, я распознаю и посчитаю КБЖУ

2️⃣ <b>Фото этикетки</b>
Пришли фото этикетки продукта для точных данных

3️⃣ <b>Текстом</b>
Напиши что съел, например:
"2 яйца, тост с маслом"
"куриная грудка 150г с гречкой"

<b>После распознавания</b> я спрошу к какому приему пищи отнести:
🌅 Завтрак
🌞 Обед
🌙 Ужин
🍎 Перекус

<b>Команды:</b>
/stats - посмотреть сводку за день
/burned 2500 - указать расход калорий (с wearables)
/weight 75.5 - записать вес
/help - эта справка

<b>Профицит калорий</b>
Чтобы видеть профицит, укажи сколько калорий потратил за день командой /burned"""

    await message.answer(help_text, parse_mode="HTML")
