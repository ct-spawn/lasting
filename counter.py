import requests as req
from xml.etree.ElementTree import fromstring, Element as xmlemlmt
import pymysql
import datetime
import time
import os

# استخدم متغيرات بيئية لتخزين معلومات قاعدة البيانات
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "lastingbeasts123")
MYSQL_USER = os.getenv("MYSQL_USER", "ct_spawn")
MYSQL_PASS = os.getenv("MYSQL_PASS", "password123")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))

def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASS,
        db=MYSQL_DATABASE,
        port=MYSQL_PORT,
    )

def create_tables():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS player_stats
                (name VARCHAR(50) PRIMARY KEY, last_played DATETIME,
                day7ago INT DEFAULT 0,
                day6ago INT DEFAULT 0,
                day5ago INT DEFAULT 0,
                day4ago INT DEFAULT 0,
                day3ago INT DEFAULT 0,
                day2ago INT DEFAULT 0,
                yestoday INT DEFAULT 0,
                today INT DEFAULT 0);''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS day
                (name VARCHAR(50) PRIMARY KEY, today INT);''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS player_night
                (name VARCHAR(50) PRIMARY KEY, last_played DATETIME,
                nightmeres INT DEFAULT 0);''')
            
            conn.commit()
    finally:
        conn.close()

def is_between(first,last):
    if first>=24 or first<0:
        return False
    if last>=24 or last<0:
        return False
    now = datetime.datetime.now()
    # تحديد وقت الساعة 6 مساءً
    six_pm = now.replace(hour=first, minute=0, second=0, microsecond=0)
    # تحديد وقت الساعة 10 صباحًا في اليوم التالي
    ten_am_next_day = (now + datetime.timedelta(days=1)).replace(hour=last, minute=0, second=0, microsecond=0)
    
    if now >= six_pm or now < ten_am_next_day.replace(day=now.day):
        return True
    return False

def is_within_time_range():
    now = datetime.datetime.now().time()
    start_time = datetime.time(17, 0)
    end_time = datetime.time(17, 30)

    return start_time <= now < end_time

def initialize_day():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM day;")
            row = cursor.fetchone()
            if row is None:
                current_day = datetime.date.today().day
                cursor.execute("INSERT INTO day VALUES (%s, %s);", ('day', current_day))
                conn.commit()
    finally:
        conn.close()

def update_week():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM player_stats;")
            rows = cursor.fetchall()
            for row in rows:
                cursor.execute('''UPDATE player_stats
                                SET day7ago = %s, day6ago = %s, day5ago = %s, day4ago = %s,
                                day3ago = %s, day2ago = %s, yestoday = %s, today = 0
                                WHERE name = %s;''',
                               (row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[0]))
            conn.commit()
    finally:
        conn.close()

def fetch_player_data():
    url = "http://api.gametracker.rs/demo/xml/server_info/135.125.128.254:27015/"
    try:
        response = req.get(url)
        response.raise_for_status()
        return fromstring(response.text)
    except req.RequestException as e:
        print(f"An error occurred while fetching player data: {e}")
        return None

def update_player_stats(root: xmlemlmt):
    conn = get_db_connection()
    try:
        for child in root.find("players_list"):
            names = child.findall("name")
            for name in names:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM player_stats WHERE name = %s;", (name.text,))
                    result = cursor.fetchone()
                    if result:
                        playtime = result[9] + 1
                        cursor.execute("UPDATE player_stats SET last_played = %s, today = %s WHERE name = %s;",
                                       (now, playtime, name.text))
                    else:
                        cursor.execute("INSERT INTO player_stats VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                                       (name.text, now, 0, 0, 0, 0, 0, 0, 0, 1))
                conn.commit()
                if is_between(18,10):
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT * FROM player_night WHERE name = %s;", (name.text,))
                        result = cursor.fetchone()
                        if result:
                            playtime = result[2] + 1
                            cursor.execute("UPDATE player_night SET last_played = %s, nightmeres = %s WHERE name = %s;",
                                        (now, playtime, name.text))
                        else:
                            cursor.execute("INSERT INTO player_night VALUES (%s, %s, %s);",
                                        (name.text, now, 0))
                    conn.commit()
                elif is_within_time_range():
                    with conn.cursor() as cursor:
                        cursor.execute("DROP TABLE IF EXISTS player_night;")
                    conn.commit()
    finally:
        conn.close()

def calc():
    root = fetch_player_data()
    if root is not None:
        update_player_stats(root)

def allwork():
    try:
        print("allwork start")
        initialize_day()
        
        while True:
            time.sleep(60)
            new_day = datetime.date.today().day
            
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT today FROM day WHERE name = 'day';")
                    row = cursor.fetchone()
                    current_day = row[0]
                    
                    if new_day != current_day:
                        update_week()
                        cursor.execute("UPDATE day SET today = %s WHERE name = 'day';", (new_day,))
                        conn.commit()
                        current_day = new_day
                    else:
                        calc()
            finally:
                conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")
