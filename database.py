import sqlite3

DB_NAME = 'barber.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT
    ) 
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        date TEXT,
        time TEXT,
        service TEXT,
        phone TEXT,
        FOREIGN KEY (user_id) REFERENCES clients(user_id)
    )
    ''')
    conn.commit()
    conn.close()

def add_name(user_id: int,name: str,phone: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO clients VALUES (?,?,?)",(user_id,name,phone))
    conn.commit()
    conn.close()

def add_booking(user_id: int,username: str, date: str,time: str,service: str,phone: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT  INTO bookings(user_id,username,date,time,service,phone) VALUES (?,?,?,?,?,?)",(user_id,username,date,time,service,phone))
    conn.commit()
    conn.close()
    
def get_user_bookings(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date,time,service FROM bookings WHERE user_id=? ",(user_id,))
    result = cursor.fetchall()
    conn.close()
    return result
    
def is_time_busy(date: str,time: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE date = ? AND time = ? ", (date,time))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_bookings_by_date(date: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time,service,username,phone FROM bookings WHERE date=? ORDER BY time",(date,))
    result = cursor.fetchall()
    conn.close()
    return result     
