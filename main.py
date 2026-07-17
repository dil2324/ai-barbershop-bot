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
    raise ValueError("The token was not found. Check the .env file")

if admin is None :
    raise ValueError("ADMIN_ID not found. Check the  .env file")

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
        types.KeyboardButton(text="Where are you located?"),
        types.KeyboardButton(text=" Services and prices")
    )
    builder.row(
        types.KeyboardButton(text="Sign up"),
        types.KeyboardButton(text="My notes")
    )
    return builder.as_markup(resize_keyboard=True)

def get_services_kb():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text = "Haircut - 3500tg", callback_data = "service_Haircut"))
    builder.add(types.InlineKeyboardButton(text = "Shaving - 5000tg", callback_data = "service_Shaving"))
    builder.add(types.InlineKeyboardButton(text = "Complex - 7000tg", callback_data = "service_Complex"))
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
    
    first_name = message.from_user.first_name if message.from_user else  "User"
    
    await message.answer (
        f"Hello {first_name}! \n "
        "This is the barbershop 'Your brand'.I'm your AI admin. How can I help you?",
        reply_markup=get_main_kb()
    )

@dp.message(F.text=="Services and prices")    
async def show_services(message: types.Message):
    text = (
        "Our services: \n\n"
        "Haircut - 4000tg\n"
        "Shaving - 3000tg\n"
        "Complex - 7500tg\n"
        "Click on 'Sign up' to select the time"
    )
    await message.answer(text)

@dp.message(F.text=="Where are you located?")
async def show_address(message: types.Message):
    await message.answer("We are located in c.Oral,Almazova st.\n We work from 10:00-21:00")
    
@dp.message(F.text == "My notes")
async def show_bookings(message: types.Message):
    if not message.from_user: 
        return
    bookings = db.get_user_bookings(message.from_user.id)
    if bookings:
        text = "Your notes\n\n"
        for date,time,service in bookings:
            text += f"{date} в {time} - {service}\n"
    else:
        text = "You don't have any records"
    await message.answer(text)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    user = message.from_user
    
    if user is None:
        return
    
    if user.id != ADMIN_ID:
        await message.answer("You don't have access")
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    bookings = db.get_bookings_by_date(today)
    
    if not bookings :
        await message.answer(f"There are no entries for today {today}")
        return
    
    text = f"Entries for today {today}: \n\n"
    for time, service, username,phone in bookings:
        text += f"{time} - {service}\n @{username}\n {phone}\n\n"
    await message.answer(text)
        

@dp.message(F.text == "Sign up")
async def start_booking(message: types.Message, state: FSMContext):
    await state.set_state(Booking.choosing_service)
    await message.answer("Choose a service", reply_markup=get_services_kb())
    
@dp.callback_query(Booking.choosing_service, F.data.startswith("service_"))
async def process_service(callback: types.CallbackQuery, state: FSMContext):
    if  callback.data is None:
        return

    service = callback.data.split("_")[1]
    await state.update_data(service=service)
    await state.set_state(Booking.choosing_master)
    
    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(f"Service: {service}\n\nSelect a master:", reply_markup=get_masters_kb()) 

@dp.callback_query(Booking.choosing_master, F.data.startswith("master_"))
async def process_master(callback: types.CallbackQuery, state: FSMContext):
    if callback.data is None:
        return
    
    master_id = int(callback.data.split("_")[1])
    await state.update_data(master_id=master_id)
    await state.set_state(Booking.choosing_date)
    
    if isinstance(callback.message, types.Message):
        await callback.message.edit_text("Choose a time:", reply_markup=get_dates_kb())
    
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
        
        await callback.message.edit_text(f"Date: {date}\n\nChoose a time:", reply_markup=get_times_kb(date, data['master_id']))

    await callback.answer()
    
@dp.callback_query(Booking.choosing_time, F.data.startswith("time_"))
async def process_time(callback: types.CallbackQuery, state: FSMContext):
    if callback.data is None:
        return
    
    time = callback.data.split("_")[1]
    await state.update_data(time=time)
    await state.set_state(Booking.getting_phone)
    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(f"Time: {time}\n\nSend your phone number for communication:")
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
    
    await message.answer(f"Done\n\n You 're signed up for: \n{data['service']}\n{data['date']} в {data['time']}\n\nWe are waiting for you!")
    await state.clear()     
    
@dp.message()
async def handle_all(message: types.Message):
    await message.answer("Unknown team. Click the button from the menu")
    
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
                await bot.send_message(user_id, f"Reminder :\nTomorrow at {time} you have {service}\n   We are waiting at the barbershop!")
                cursor.execute("UPDATE bookings SET reminded_24h=1 WHERE id=?",(booking_id,))
            except:
                pass
        
        today = now.strftime("%Y-%m-%d")
        three_hours_later = (now + timedelta(hours=3)).strftime("%H:%M")
        cursor.execute("SELECT id, user_id, time, service FROM bookings WHERE date=? AND time=? AND reminded_3h=0", (today,three_hours_later))
        bookings_3h = cursor.fetchall()
        
        for booking_id, user_id, time, service in bookings_3h:
            try:
                await bot.send_message(user_id, f"After 3 hours.\n Today at {time} : {service}")
                cursor.execute("UPDATE bookings SET reminded_3h=1 WHERE id=?", (booking_id,))
            except:
                pass
        
        
        conn.commit()
        conn.close()
        
        await asyncio.sleep(600)  
            

async def main():
    db.init_db()
    asyncio.create_task(reminder_task())
    print("The bot is running...")
    await dp.start_polling(bot) 
    
if __name__ == "__main__":
    asyncio.run(main())
