import asyncio
from aiogram import Bot,Dispatcher, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command 
from aiogram.utils.keyboard import (
    ReplyKeyboardBuilder,InlineKeyboardBuilder
    )
import database as db
from dotenv import load_dotenv
import os
from datetime import datetime , timedelta


load_dotenv()
TOKEN=os.getenv("BOT_TOKEN")
admin = os.getenv("ADMIN_ID")

if TOKEN is None :
    raise ValueError("Токен не найден. Проверь файл .env")

if admin is None :
    raise ValueError("ADMIN_ID не найден. Проверь файл .env")

ADMIN_ID = int(admin)

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Booking(StatesGroup):
    choosing_service= State()
    choosing_master = State()
    choosing_date = State()
    choosing_time = State()
    getting_phone= State()

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

def get_services_kb():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text = "Стрижка - 3500тг", callback_data = "service_Стрижка"))
    builder.add(types.InlineKeyboardButton(text = "Бритье - 5000тг", callback_data = "service_Бритье"))
    builder.add(types.InlineKeyboardButton(text = "Комплекс - 7000тг", callback_data = "service_Комплекс"))
    builder.adjust(1)
    return builder.as_markup()

def get_masters_kb():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM masters")
    masters = cursor.fetchall()
    conn.close()
    
    builder = InlineKeyboardBuilder()
    for id, name in masters:
        builder.add(types.InlineKeyboardButton(text=name, callback_data=f"master_{id}"))
    builder.adjust(2)
    return builder.as_markup()
    

def get_dates_kb():
    builder = InlineKeyboardBuilder()
    for i in range(1,8):
        date = datetime.now() + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        date_show= date.strftime("%d.%m")
        builder.add(types.InlineKeyboardButton(text = date_show,callback_data=f"date_{date_str}"))
    builder.adjust(3)
    return builder.as_markup()

def get_times_kb(date: str,master_id: int ):
    builder = InlineKeyboardBuilder()
    times = ["12:00" , "14:00", "15:00","16:00","18:00","20:00"]
    for time in times:
        if not db.is_time_busy(date,time,master_id):
            builder.add(types.InlineKeyboardButton(text=time,callback_data=f"time_{time}"))
    builder.adjust(3)
    return builder.as_markup()
    

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    
    first_name = message.from_user.first_name if message.from_user else  "Пользователь"
    
    await message.answer (
        f"Привет {first_name}! \n "
        "Это барбершоп 'ТВОЙ БРЕНД'. Я ваш AI-админ. Чем помочь?",
        reply_markup=get_main_kb()
    )

@dp.message(F.text=="Услуги и цены")    
async def show_services(message: types.Message):
    text = (
        "Наши услуги: \n\n"
        "Стрижка - 4000тг\n"
        "Бритье - 3000 тг\n"
        "Комплекс - 7500тг\n"
        "Нажми 'Записаться' чтобы выбрать время"
    )
    await message.answer(text)

@dp.message(F.text=="Где вы находитесь?")
async def show_address(message: types.Message):
    await message.answer("Мы находимся: г.Орал ул. Алмазова.\n Работаем с 10:00-21:00")
    
@dp.message(F.text == "Мои записи")
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

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    user = message.from_user
    
    if user is None:
        return
    
    if user.id != ADMIN_ID:
        await message.answer("У вас нет доступа")
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    bookings = db.get_bookings_by_date(today)
    
    if not bookings :
        await message.answer(f"На сегодня {today} записей нет")
        return
    
    text = f"Записи на сегодня {today}: \n\n"
    for time, service, username,phone in bookings:
        text += f"{time} - {service}\n @{username}\n {phone}\n\n"
    await message.answer(text)
        

@dp.message(F.text == "Записаться")
async def start_booking(message: types.Message, state: FSMContext):
    await state.set_state(Booking.choosing_service)
    await message.answer("Выбери услугу", reply_markup=get_services_kb())
    
@dp.callback_query(Booking.choosing_service, F.data.startswith("service_"))
async def process_service(callback: types.CallbackQuery, state: FSMContext):
    if  callback.data is None:
        return

    service = callback.data.split("_")[1]
    await state.update_data(service=service)
    await state.set_state(Booking.choosing_master)
    
    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(f"Услуга: {service}\n\nВыбери мастера:", reply_markup=get_masters_kb()) 

@dp.callback_query(Booking.choosing_master, F.data.startswith("master_"))
async def process_master(callback: types.CallbackQuery, state: FSMContext):
    if callback.data is None:
        return
    
    master_id = int(callback.data.split("_")[1])
    await state.update_data(master_id=master_id)
    await state.set_state(Booking.choosing_date)
    
    if isinstance(callback.message, types.Message):
        await callback.message.edit_text("Выбери дату:", reply_markup=get_dates_kb())
    
    await callback.answer()

@dp.callback_query( Booking.choosing_date, F.data.startswith("date_"))
async def process_date(callback: types.CallbackQuery, state: FSMContext):
    if callback.data is None:
        return
    
    date = callback.data.split("_")[1]
    await state.update_data(date=date)
    await state.set_state(Booking.choosing_time)
    
    data = await state.get_data()
    if isinstance(callback.message, types.Message):
        
        await callback.message.edit_text(f"Дата: {date}\n\nВыбери время:", reply_markup=get_times_kb(date, data['master_id']))

    await callback.answer()
    
@dp.callback_query(Booking.choosing_time, F.data.startswith("time_"))
async def process_time(callback: types.CallbackQuery, state: FSMContext):
    if callback.data is None:
        return
    
    time = callback.data.split("_")[1]
    await state.update_data(time=time)
    await state.set_state(Booking.getting_phone)
    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(f"Время: {time}\n\nОтправь свой номер телефона для связи:")
    await callback.answer()

@dp.message(Booking.getting_phone)
async def process_phone(message: types.Message, state: FSMContext):
    
    if message.from_user is None:
        return
    
    phone = message.text
    
    if phone is None:
        return
    
    data = await state.get_data()
    
    name = message.from_user.first_name or "User"
    db.add_name( message.from_user.id,name, phone)
    
    db.add_booking(
        user_id=message.from_user.id,
        username = message.from_user.username or "",
        service=data['service'],
        date=data['date'],
        time=data['time'],
        phone=phone,
        master_id=data['master_id']
    )
    
    await message.answer(f"Готово\n\n Ты записан на: \n{data['service']}\n{data['date']} в {data['time']}\n\nЖдем тебя!")
    await state.clear()     
    
@dp.message()
async def handle_all(message: types.Message):
    await message.answer("Неизвестная команда. Нажми кнопку из меню")
    
async def reminder_task():
    while True:
        now = datetime.now()
        
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id,user_id,time,service FROM bookings WHERE date=? AND reminded_24h=0",(tomorrow,))
        bookings_24h = cursor.fetchall()
        
        for booking_id , user_id,time, service in bookings_24h:
            try:
                cursor.execute("SELECT user_id FROM bookings WHERE id=?",(booking_id,))
                user_id = cursor.fetchone()[0]
                await bot.send_message(user_id, f"Напоминание :\nЗавтра в {time} у тебя {service}\n Ждем в барбершопе!")
                cursor.execute("UPDATE bookings SET reminded_24h=1 WHERE id=?",(booking_id,))
            except:
                pass
        
        today = now.strftime("%Y-%m-%d")
        three_hours_later = (now + timedelta(hours=3)).strftime("%H:%M")
        cursor.execute("SELECT id, user_id, time, service FROM bookings WHERE date=? AND time=? AND reminded_3h=0", (today,three_hours_later))
        bookings_3h = cursor.fetchall()
        
        for booking_id, user_id, time, service in bookings_3h:
            try:
                await bot.send_message(user_id, f" Через 3 часа.\n Сегодня в {time} : {service}")
                cursor.execute("UPDATE bookings SET reminded_3h=1 WHERE id=?", (booking_id,))
            except:
                pass
        
        
        conn.commit()
        conn.close()
        
        await asyncio.sleep(600)  
            

async def main():
    db.init_db()
    asyncio.create_task(reminder_task())
    print("Бот запущен...")
    await dp.start_polling(bot) 
    
if __name__ == "__main__":
    asyncio.run(main())
    
