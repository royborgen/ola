#!./venv/bin/python3
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import sys
import bcrypt
from olauser import hashpass, update_users
from passcheck import is_strong_password


app = Flask(__name__)
app.secret_key = os.urandom(24)
@app.route('/')
def home():

    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('overview.html')


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
