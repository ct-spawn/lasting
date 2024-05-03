import signal
from flask import Flask,render_template,send_from_directory,request
from os.path import join
from markupsafe import escape
from os import _exit
import pymysql
from counter import thread_1,thread_2,MYSQL_HOST,MYSQL_USER,MYSQL_PASS,MYSQL_DATABASE

MAX_SIZE=2854

def get_top15():
    conn = pymysql.connect( 
        host=MYSQL_HOST, 
        user=MYSQL_USER,  
        password = MYSQL_PASS, 
        db=MYSQL_DATABASE,
        port=18000, 
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
        port=18000, 
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

def get_players(lines):
    allrows=[]
    conn = pymysql.connect( 
        host=MYSQL_HOST, 
        user=MYSQL_USER,  
        password = MYSQL_PASS, 
        db=MYSQL_DATABASE,
        port=18000, 
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


thread_1.start()
thread_2.start()
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
