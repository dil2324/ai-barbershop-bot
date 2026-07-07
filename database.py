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
        date TEXT,
        time TEXT,
        service TEXT,
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

def add_booking(user_id: int, date: str,time: str,service: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT  INTO bookings(user_id,date,time,service) VALUES (?,?,?,?)",(user_id,date,time,service))
    conn.commit()
    conn.close()
    
def get_user_bookings(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date,time,service FROM bookings WHERE user_id=? ",(user_id,))
    result = cursor.fetchall()
    conn.close()
    return result
    
