#!./venv/bin/python3
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import sys
import bcrypt
from olauser import hashpass, update_users
from olakafka import * 
from passcheck import is_strong_password


app = Flask(__name__)
app.secret_key = os.urandom(24)
@app.route('/', methods=['GET', 'POST'])
def home():
    
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        messages = []    

        train_number  = request.form['train_number']
        station  = request.form['station']
        date_from  = request.form['date_from']
        time_from  = request.form['time_from']
        date_to  = request.form['date_to']
        time_to  = request.form['time_to']
        search  = request.form['search']
        
        
        if date_from !="": 
            if time_from !="":
                date_from = date_from + " " + time_from + ":00"
            else:
                date_from = date_from + " " + "00:00:00"
        if date_to !="": 
            if time_to !="":
                date_to = date_to + " " + time_to + ":00"
            else: 
                date_to = date_to + " " + "00:00:00"
        
        if search == "True": 
            #kafka_message = GetKafkaMessages(date_start, date_stop)
            with open("sample_one_hour.json", "r") as kfk_messages:
                for line in kfk_messages:
                    messages.append(json.loads(line))
            kfk_messages.close()
            
        if kfk_messages: 
            result = True
            
            #for line in kfka_message:
            #    message.append(json.load(line))
        

        searchfilter = {'trainnumber':train_number, 'station':station, 'date_from':date_from, 'date_to':date_to}
        
        #filter the data and make i readable for humans
        filteredData = filterKafkaMessages(messages, searchfilter)

        return render_template('overview.html', messages=filteredData, result=result)


@app.route('/main', methods=['POST'])
def do_login():
    session.clear()
    session['logged_in'] = False
    basedir = os.path.abspath(os.path.dirname(__file__))
    data_file = os.path.join(basedir, 'users.db')
    
    bytes_password = request.form['password'].encode('utf-8')

    # Read from the database and check the password
    with open('users', "r") as file:
        for line in file.readlines():
            db_username, db_fullname, db_hashed_password, db_changepass = line.strip().split(":")
            db_hashed_password = db_hashed_password.encode('utf-8')

            if request.form['username'] == db_username: 
                if bcrypt.checkpw(bytes_password, db_hashed_password):
                    session['fullname'] = db_fullname
                    session['username'] = db_username
                    
                    if db_changepass == "1":
                        return render_template('changepass.html')
                    else:
                        session['logged_in'] = True
    

    if session['logged_in'] == True:
        return render_template('overview.html')
    
    else:
        session['login_message'] = "Feil brukernavn eller passord"
        return home()


@app.route('/changepass', methods=['POST'])
def changepass():
    username = session['username']
    fullname = session['fullname']
    newpass = request.form['newpass']
    repeat_pass = request.form['repeat_pass']
    
    if is_strong_password(newpass): 
        hashed_newpass = hashpass(newpass)
        update_users(username, fullname, hashed_newpass, False, 0)
        session['logged_in'] = True  
        return home()
    else: 
        session['login_message'] = "Passordet ditt tilfredstiller ikke kompleksitetskravene"
        return render_template('changepass.html')
    


@app.route('/logout', methods=['POST'])
def logout():
    #session.pop('logged_in', None)
    session.clear()
    return home()


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=5000)
