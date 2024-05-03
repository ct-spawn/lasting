import requests as req
from xml.etree.ElementTree import fromstring
import pymysql
import datetime
import threading
import time


MYSQL_HOST = "lastingbeasts-kali-f4ca.f.aivencloud.com"
MYSQL_DATABASE = "defaultdb"
MYSQL_USER = "avnadmin"
MYSQL_PASS = "AVNS_5vn2nFqxFQiAVQAAHRT"



conn_global = pymysql.connect( 
        host=MYSQL_HOST, 
        user=MYSQL_USER,  
        password = MYSQL_PASS, 
        db=MYSQL_DATABASE,
        port=18000
        ) 

cursor_global = conn_global.cursor()
# إنشاء جدول لتخزين بيانات اللاعبين
cursor_global.execute('''CREATE TABLE IF NOT EXISTS player_stats
                (name varchar(50) PRIMARY KEY, last_played DATETIME,
                day7ago INT DEFAULT 0,
                day6ago INT DEFAULT 0,
                day5ago INT DEFAULT 0,
                day4ago INT DEFAULT 0,
                day3ago INT DEFAULT 0,
                day2ago INT DEFAULT 0,
                yestoday INT DEFAULT 0,
                today INT DEFAULT 0);''')
conn_global.commit()
cursor_global.close()

cursor_global = conn_global.cursor()
# إنشاء جدول لتخزين بيانات اللاعبين
cursor_global.execute('''CREATE TABLE IF NOT EXISTS day
                (name varchar(50) PRIMARY KEY , today INT);''')
conn_global.commit()
cursor_global.close()

conn_global.close()

def founder_file():
    conn = pymysql.connect( 
        host=MYSQL_HOST, 
        user=MYSQL_USER,  
        password = MYSQL_PASS, 
        db=MYSQL_DATABASE,
        port=18000, 
        )
    cursor = conn.cursor()
    # تنفيذ الاستعلام لاختيار كل الصفوف
    cursor.execute("SELECT * FROM day;")
    row = cursor.fetchone()
    cursor.close()
    if row is None:
        cursor = conn.cursor()
        current_day = datetime.date.today().day
        cursor.execute("INSERT INTO day VALUES (%s, %s);", ('day',current_day ))
        conn.commit()
        cursor.close()
    conn.close()
founder_file()

def update_week():
    conn = pymysql.connect( 
        host=MYSQL_HOST, 
        user=MYSQL_USER,  
        password = MYSQL_PASS, 
        db=MYSQL_DATABASE,
        port=18000, 
        )
    cursor = conn.cursor()
    # تنفيذ الاستعلام لاختيار كل الصفوف
    cursor.execute("SELECT * FROM player_stats;")
    # استرداد كافة الصفوف
    rows = cursor.fetchall()
    cursor.close()
    for row in rows:
        cursor = conn.cursor()
        cursor.execute(f"""UPDATE player_stats
                           SET day7ago = {row[3]}, day6ago = {row[4]},day5ago = {row[5]},day4ago = {row[6]},
                           day3ago = {row[7]},day2ago = {row[8]},yestoday = {row[9]},today = 0 WHERE name='{row[0]}';
                           """)
        conn.commit()
        cursor.close()
    conn.close()
def check_new_day():
    print("check_new_day start")
    current_day=0
    while True:
        founder_file()
        conn = pymysql.connect( 
            host=MYSQL_HOST, 
            user=MYSQL_USER,  
            password = MYSQL_PASS, 
            db=MYSQL_DATABASE,
        port=18000, 
            )
        
        cursor = conn.cursor()
        # تنفيذ الاستعلام لاختيار كل الصفوف
        cursor.execute("SELECT * FROM day where name='day';")
        row = cursor.fetchone()
        cursor.close()
        current_day=row[1]
        time.sleep(60)
        new_day = datetime.date.today().day
        if new_day != current_day:
            cursor = conn.cursor()
            cursor.execute(f"""UPDATE day
                            SET today = {new_day} WHERE name='day';
                            """)
            conn.commit()
            cursor.close()
            update_week()
        conn.close()
thread_1 = threading.Thread(target=check_new_day, args=())
#thread_1.start()

def calc():
    reqo=None
    url="http://api.gametracker.rs/demo/xml/server_info/135.125.128.254:27015/"
    try:
        reqo=req.get(url)
    except:
        pass
    if reqo is not None:
        if reqo.status_code==200:
            conn2 = pymysql.connect( 
                host=MYSQL_HOST, 
                user=MYSQL_USER,  
                password = MYSQL_PASS, 
                db=MYSQL_DATABASE,
        port=18000, 
                )
            text=reqo.text
            root = fromstring(text)
            for child in root.find("players_list"):
                names=child.findall("name")
                for name in names:
                    # الحصول على الوقت الحالي
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor = conn2.cursor()
                    # استعراض اللاعب من قاعدة البيانات
                    cursor.execute("SELECT * FROM player_stats WHERE name=%s;", (name.text,))
                    result = cursor.fetchone()
                    cursor.close()
                    cursor = conn2.cursor()
                    if result:
                        # إذا كان اللاعب موجودًا، قم بتحديث وقت اللعب والوقت الأخير
                        playtime = result[9] + 1  # زيادة الوقت بدقيقة واحدة
                        last_played = now
                        cursor.execute("UPDATE player_stats SET last_played=%s, today=%s WHERE name=%s;", ( last_played,playtime, name.text))
                    else:
                        # إذا كان اللاعب غير موجود، قم بإضافته إلى قاعدة البيانات
                        playtime = 1  # البدء بوقت اللعب 1 دقيقة
                        last_played = now
                        cursor.execute("INSERT INTO player_stats VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (name.text,last_played,0,0,0,0,0,0,0,0 ))
                    conn2.commit()
                    cursor.close()
            conn2.close()
def work_calc():
    print("work_calc start")
    while True:
        calc()
        time.sleep(60)
thread_2 = threading.Thread(target=work_calc, args=())
#thread_2.start()
print("ready ..")

