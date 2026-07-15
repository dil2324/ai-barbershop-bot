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
    CREATE TABLE IF NOT EXISTS masters(
        id INT PRIMARY KEY,
        name TEXT
    )           
    ''')
                 
    cursor.execute("INSERT OR IGNORE INTO masters (id, name) VALUES (1, 'Dias')")
    cursor.execute("INSERT OR IGNORE INTO masters (id,name) VALUES (2, 'Arman')")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        date TEXT,
        time TEXT,
        service TEXT,
        phone TEXT,
        master_id INTEGER,
        reminded_24h INTEGER DEFAULT 0,
        reminded_3h INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES clients(user_id),
        FOREIGN KEY (master_id) REFERENCES masters(id)
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

def add_booking(user_id: int,username: str, date: str,time: str,service: str,phone: str, master_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT  INTO bookings(user_id,username,date,time,service,phone,master_id) VALUES (?,?,?,?,?,?,?)",(user_id,username,date,time,service,phone,master_id))
    conn.commit()
    conn.close()
    
def get_user_bookings(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date,time,service FROM bookings WHERE user_id=? ",(user_id,))
    result = cursor.fetchall()
    conn.close()
    return result
    
def is_time_busy(date: str,time: str, master_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE date = ? AND time = ? AND master_id = ? ", (date,time,master_id))
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
