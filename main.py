from flask import Flask,render_template,request
from flask import redirect,url_for
import mysql.connector
from datetime import datetime
import random
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto import Random
import os
import base64
import random
import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders
import datetime

UPLOAD_FOLDER = 'static/file/'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mydb = mysql.connector.connect(host="localhost",user="root",password="",database="security")
mycursor = mydb.cursor()

BS = 16
pad = lambda s: bytes(s + (BS - len(s) % BS) * chr(BS - len(s) % BS), 'utf-8')
unpad = lambda s : s[0:-ord(s[-1:])]

class AESCipher:

    def __init__( self, key ):
        self.key = bytes(key, 'utf-8')

    def encrypt( self, raw ):
        raw = pad(raw)
        iv = Random.new().read( AES.block_size )
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw ) )

    def decrypt( self, enc ):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[16:] )).decode('utf8')

cipher = AESCipher('mysecretpassword')

@app.route('/')
@app.route('/main')
@app.route('/sender')
def sender():
    return render_template('login.html')

@app.route('/register')
def sreg():
    return render_template('register.html')

@app.route('/log',methods=['POST','GET'])
def svalid():
    global data1
    if request.method == 'POST':
        data1 = request.form.get('username')
        data2 = request.form.get('password')
        sql = "SELECT * FROM `send` WHERE `name` = %s AND `password` = %s"
        val = (data1, data2)
        mycursor.execute(sql,val)
        account = mycursor.fetchall()
        if account:
            return render_template('admin.html',u=data1)
        else:
            return render_template('login.html',msg = 'Invalid Username or Password')

@app.route('/reg',methods=['POST','GET'])
def sregform():
    if request.method == 'POST':
        name = request.form.get('username')
        mail = request.form.get('email')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        dob= request.form.get('dob')
        password = request.form.get('password')
        sql = "INSERT INTO send (`name`, `email`, `mobile`, `gender`, `dob`, `password`) VALUES (%s, %s, %s, %s, %s, %s)"
        val = (name, mail, phone, gender, dob, password)
        mycursor.execute(sql, val)
        mydb.commit()
        return render_template('login.html')

@app.route('/uploadpage')
def uppage():
    return render_template('admin.html')

@app.route('/upload',methods=['POST','GET'])
def upload():
    global encrypted
    if request.method == 'POST':
        s_name = data1
        file_name = request.form.get('filename')
        file = request.files['file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        encrypted = cipher.encrypt(file_path)
        double_encrypted = cipher.encrypt(str(encrypted))
        file.save(file_path)
        sql = "SELECT * FROM `files` WHERE `f_name` = %s"
        val = (file_name,)
        mycursor.execute(sql,val)
        account = mycursor.fetchone()
        if account:
            return render_template('admin.html',msg='File Name Already Exists')
        else:
            now = datetime.datetime.now()
            sql = "INSERT INTO files (`date`, `s_name`, `f_name`, `f_path`) VALUES (%s, %s, %s, %s)"
            val = (now, s_name, file_name, encrypted)
            mycursor.execute(sql, val)
            mydb.commit()
            return render_template('admin.html',msg='File Upload Successfully')

@app.route('/file')
def file():
    sql = "SELECT * FROM `files` WHERE `s_name` = %s "
    val = (data1,)
    mycursor.execute(sql,val)
    result = mycursor.fetchall()
    if result:
        return render_template('file.html',data = result)
    else:
        return render_template('file.html',msg = 'No Data')

@app.route('/req')
def re():
    sql = "SELECT * FROM `req` WHERE `s_name` = %s AND `req` = %s "
    val = (data1,'Yes')
    mycursor.execute(sql,val)
    account = mycursor.fetchall()
    if account:
        return render_template('verify.html',data = account)
    else:
        return render_template('verify.html',msg = 'No Data')

@app.route('/key',methods=['POST','GET'])
def key():
    global r
    if request.method == 'POST':
        fname = request.form.get('fname')
        sql = "INSERT INTO req (`s_name`, `f_name`, `req`) VALUES (%s, %s, %s)"
        val = (data1, fname, 'Yes')
        mycursor.execute(sql, val)
        mydb.commit()
        sql = "SELECT * FROM `send` WHERE `name` = %s "
        val = (data1,)
        mycursor.execute(sql,val)
        account = mycursor.fetchall()
        if account:
            for i in account:
                r = random.randint(100000,999999)
                ema = i[2]
                fromaddr = "digitalcertificate128@gmail.com"
                toaddr = ema
                msg = MIMEMultipart()  
                msg['From'] = fromaddr 
                msg['To'] = toaddr 
                msg['Subject'] = 'Security Key From Sender'
                body = f"This is your OTP for {fname} : {r} \nPlease enter properly."
                msg.attach(MIMEText(body, 'plain')) 
                s = smtplib.SMTP('smtp.gmail.com', 587) 
                s.starttls() 
                s.login(fromaddr, "jzuxgewjwjcmukdh") 
                text = msg.as_string() 
                s.sendmail(fromaddr, toaddr, text) 
                s.quit()
            return render_template('file.html')

@app.route('/down',methods=['POST','GET'])
def down():
    key1 = r
    if request.method == 'POST':
        fname = request.form.get('fname')
        key = request.form.get('key')
        sql = "UPDATE `req` SET `req` = %s WHERE f_name = %s"
        val = ('No', fname)
        mycursor.execute(sql, val)
        mydb.commit()
        if key1 == int(key):
            sql = "SELECT * FROM files WHERE `f_name` = %s"
            val = (fname ,)
            mycursor.execute(sql,val)
            result = mycursor.fetchall()
            if result:
                for i in result:
                    filea = i[4]
                    print(filea)
                    decrypted = cipher.decrypt(filea)
                    return render_template('download.html',fpath=decrypted)
            else:
                return 'No Data'
        else:
            return 'Wrong Key!'
    else:
        return 'Error!'

@app.route('/delete',methods = ['POST','GET'])
def delete():
    if request.method == 'POST':
        filename = request.form.get('filename')
        sql = 'DELETE FROM `files` WHERE  `f_name` = %s'
        val = (filename,)
        mycursor.execute(sql,val)
        mydb.commit()
        return redirect(url_for('file'))

if __name__ == '__main__':
    app.run(debug=True)
