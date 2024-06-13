import signal
from flask import Flask,render_template,send_from_directory,request
from os.path import join
from markupsafe import escape
from os import _exit
import pymysql
from counter import create_tables,allwork,MYSQL_HOST,MYSQL_USER,MYSQL_PASS,MYSQL_DATABASE,MYSQL_PORT
import threading
import time
import datetime

MAX_SIZE=2854

def days_until_saturday():
    # الحصول على اليوم الحالي من الأسبوع (0 لليوم الاثنين، 6 لليوم الأحد)
    today = datetime.datetime.now().weekday()
    
    # اليوم السبت هو الرقم 5
    saturday = 5
    
    # حساب الأيام المتبقية حتى يوم السبت
    days_left = (saturday - today) % 7
    
    # إذا كان اليوم هو السبت، نعيد 7 أيام حتى السبت التالي
    if days_left == 0:
        days_left = 7
    
    return days_left

def check_table_exist(table_name):
    conn = pymysql.connect( 
        host=MYSQL_HOST, 
        user=MYSQL_USER,  
        password = MYSQL_PASS, 
        db=MYSQL_DATABASE,
        port=MYSQL_PORT, 
        )
    try:      
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s;
            """, (MYSQL_DATABASE, table_name))
            result = cursor.fetchone()
            conn.close()
            return result[0] == 1
    except:
        conn.close()


def get_top15():
    conn = pymysql.connect( 
        host=MYSQL_HOST, 
        user=MYSQL_USER,  
        password = MYSQL_PASS, 
        db=MYSQL_DATABASE,
        port=MYSQL_PORT, 
        )
    Sql="""SELECT name,day7ago,day6ago,day5ago,day4ago,day3ago,day2ago,yestoday,today,last_played,
        day7ago+day6ago+day5ago+day4ago+day3ago+day2ago+yestoday as days_Total
        FROM player_stats ORDER by days_Total DESC;"""
    cursor = conn.cursor()
    cursor.execute(Sql)
    rows = cursor.fetchmany(15)
    cursor.close()
    conn.close()
    rows2=[]
    for row in rows:
        row1=list(row)
        row1[0]=escape(row1[0])
        rows2.append(row1)
    return rows2

def get_top15_daily():
    conn = pymysql.connect( 
        host=MYSQL_HOST, 
        user=MYSQL_USER,  
        password = MYSQL_PASS, 
        db=MYSQL_DATABASE,
        port=MYSQL_PORT, 
        )
    Sql="""SELECT name,today,last_played 
        FROM player_stats ORDER by today DESC;"""
    cursor = conn.cursor()
    cursor.execute(Sql)
    rows = cursor.fetchmany(15)
    cursor.close()
    conn.close()
    rows2=[]
    for row in rows:
        row1=list(row)
        row1[0]=escape(row1[0])
        rows2.append(row1)
    return rows2

def get_top15_nightly():
    try:
        if check_table_exist("player_night"):
            conn = pymysql.connect( 
                host=MYSQL_HOST, 
                user=MYSQL_USER,  
                password = MYSQL_PASS, 
                db=MYSQL_DATABASE,
                port=MYSQL_PORT, 
                )
            Sql="""SELECT name,nightmeres,last_played 
                FROM player_night ORDER by nightmeres DESC;"""
            cursor = conn.cursor()
            cursor.execute(Sql)
            rows = cursor.fetchmany(15)
            cursor.close()
            conn.close()
            rows2=[]
            for row in rows:
                row1=list(row)
                row1[0]=escape(row1[0])
                rows2.append(row1)
            return rows2
        else:
            return []
    except:
        return []

def get_players(lines):
    allrows=[]
    conn = pymysql.connect( 
        host=MYSQL_HOST, 
        user=MYSQL_USER,  
        password = MYSQL_PASS, 
        db=MYSQL_DATABASE,
        port=MYSQL_PORT, 
        )
    lines01=[]
    for line in lines:
        if str(line).strip()!="":
            lines01.append(line)
    stro=""
    lines01=list(set(lines01))
    count=len(lines01)
    if count==0:
        conn.close()
        return allrows
    
    for i, line in enumerate(lines01):
        if i+1==count:
            stro+=f""" Select name, day7ago,day6ago,day5ago,day4ago,day3ago,day2ago,yestoday,today,last_played,
                day7ago+day6ago+day5ago+day4ago+day3ago+day2ago+yestoday as days_Total FROM player_stats Where name like '%{line}%' """
        else:
            stro+=f""" Select name, day7ago,day6ago,day5ago,day4ago,day3ago,day2ago,yestoday,today,last_played,
            day7ago+day6ago+day5ago+day4ago+day3ago+day2ago+yestoday as days_Total FROM player_stats Where name like '%{line}%'
            Union """
    Sql=f"""Select name,day7ago,day6ago,day5ago,day4ago,day3ago,day2ago,yestoday,today,last_played,days_Total
            from({stro}) results ORDER by days_Total DESC;"""
    cursor = conn.cursor()
    cursor.execute(Sql)
    rows = cursor.fetchall()
    cursor.close()
    for row in rows:
        row1=list(row)
        row1[0]=escape(row1[0])
        allrows.append(row1)
    conn.close()
    return allrows



def handler(signum, frame):    

    print("CTRL+C")
    _exit(1)

signal.signal(signal.SIGINT, handler)
create_tables()
def monitor_and_restart_thread():
    global thread_1
    while True:
        if not thread_1.is_alive():
            print("Thread allwork has stopped. Restarting...")
            thread_1 = threading.Thread(target=allwork)
            thread_1.start()
        time.sleep(5)  # تحقق كل 5 ثوانٍ

thread_1 = threading.Thread(target=allwork)
thread_1.start()
time.sleep(5)
monitoring_thread = threading.Thread(target=monitor_and_restart_thread)
monitoring_thread.start()

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(405)
def not_found1(e):
    return render_template('405.html'), 405

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/search")
def search():
    return render_template("cos.html")

@app.route("/top15")
def top15():
    rows=get_top15()
    return render_template("top15.html",rows=rows)

@app.route("/top15today")
def top15today():
    rows=get_top15_daily()
    return render_template("top15today.html",rows=rows)

@app.route("/top15night")
def top15night():
    rows=get_top15_nightly()
    return render_template("top15night.html",rows=rows,remino=days_until_saturday())

@app.route("/players",methods=["POST"])
def players():
    info=request.form.get("search").strip()
    if len(info)>MAX_SIZE:
        return render_template("error.html",title="Overflow",para="Please do not write more than 50 lines or fill the space more than necessary") , 400
    elif len(info)==0:
        return render_template("error.html",title="Empty request",para="Please write the names of the players in each line, or at least the name of one player") , 400
    lines=str(info).replace("\r","")
    lines=str(lines).split("\n")
    rows=get_players(lines)
    return render_template("top.html",rows=rows)

app.run(host="0.0.0.0",port=5000,debug=False)
