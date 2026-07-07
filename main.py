import asyncio
from aiogram import Bot,Dispatcher, types
from aiogram.filters import Command 
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import database as db

TOKEN=""

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_main_kb():
    builder= ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Где вы находитесь?"),
        types.KeyboardButton(text="Услуги и цены")
    )
    builder.row(
        types.KeyboardButton(text="Записаться"),
        types.KeyboardButton(text="Мои записи")
    )
    
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    
    first_name = message.from_user.first_name if message.from_user else  "Пользователь"
    
    await message.answer (
        f"Привет {first_name}! \n "
        "Это барбершоп 'ТВОЙ БРЕНД'. Я ваш AI-админ. Чем помочь?",
        reply_markup=get_main_kb()
    )

    
async def show_services(message: types.Message):
    text = (
        "Наши услуги: \n\n"
        "Стрижка - 4000тг\n"
        "Бритье - 3000 тг\n"
        "Комплекс - 7500тг\n"
        "Нажми 'Записаться' чтобы выбрать время"
    )
    await message.answer(text)


async def show_address(message: types.Message):
    await message.answer("Мы находимся: г.Орал ул. твоя 12.\n Работаем с 10:00-21:00")
    

async def show_bookings(message: types.Message):
    if not message.from_user: 
        return
    bookings = db.get_user_bookings(message.from_user.id)
    if bookings:
        text = "Твои записи\n\n"
        for date,time,service in bookings:
            text += f"{date} в {time} - {service}\n"
    else:
        text = "У вас нет записей"
    await message.answer(text)
    

@dp.message()
async def handle_all(message: types.Message):
    if message.text == "Услуги и цены":
        await show_services(message)
    elif message.text == "Где вы находитесь?":
        await show_address(message)
    elif message.text == "Мои записи":
        await show_bookings(message)
    elif message.text == "Записаться":
        await message.answer("Скро добавлю сюда выбор для даты и время")
    else:
        print("Неизвестная команда")
            

async def main():
    db.init_db()
    print("Бот запущен...")
    await dp.start_polling(bot) 
    
if __name__ == "__main__":
    asyncio.run(main())
    