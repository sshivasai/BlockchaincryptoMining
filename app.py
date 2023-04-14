

#import flask dependencies for web GUI
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from passlib.hash import sha256_crypt
from functools import wraps
import pypyodbc as odbc
#import other functions and classes
from sqlhelpers import *
from forms import *

#other dependencies
import time

#initialize the app
app = Flask(__name__)

def makeconnection():
    #configure mssql
    server = 'DESKTOP-EPDTTFN'
    database = 'crypto'
    connection_string = 'DRIVER={ODBC Driver 17 for SQL Server}; \
    SERVER='+ server +'; \
    DATABASE='+ database +';\
    Trusted_Connection=yes;'
    conn = odbc.connect(connection_string)
    #print(conn.cursor())
    return conn

#wrap to define if the user is currently logged in from session
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, please login.", "danger")
            return redirect(url_for('login'))
    return wrap

#log in the user by updating session
def log_in_user(username):
    users = Table("users", "name", "email", "username", "password")
    user = users.getone("username", username)

    session['logged_in'] = True
    session['username'] = username
    session['name'] = user.get('name')
    session['email'] = user.get('email')

#Registration page
@app.route("/register", methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    users = Table("users", "name", "email", "username", "password")

    #if form is submitted
    if request.method == 'POST' and form.validate():
        #collect form data
        username = form.username.data
        email = form.email.data
        name = form.name.data

        #make sure user does not already exist
        if isnewuser(username):
            #add the user to mssql and log them in
            password = sha256_crypt.encrypt(form.password.data)
            users.insert(name,email,username,password)
            log_in_user(username)
            return redirect(url_for('dashboard'))
        else:
            flash('User already exists', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html', form=form)

#Login page
@app.route("/login", methods = ['GET', 'POST'])
def login():
    #if form is submitted
    if request.method == 'POST':
        #collect form data
        username = request.form['username']
        candidate = request.form['password']

        #access users table to get the user's actual password
        users = Table("users", "name", "email", "username", "password")
        user = users.getone("username", username)
        if user : 
            accPass = user.get('password')

        #if the password cannot be found, the user does not exist
            if accPass is None:
                flash("Username is not found", 'danger')
                return redirect(url_for('login'))
            else:
                #verify that the password entered matches the actual password
                if sha256_crypt.verify(candidate, accPass):
                    #log in the user and redirect to Dashboard page
                    log_in_user(username)
                    flash('You are now logged in.', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    #if the passwords do not match
                    flash("Invalid password", 'danger')
                    return redirect(url_for('login'))
        else:
            flash("Username is not found", 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

#Transaction page
@app.route("/transaction", methods = ['GET', 'POST'])
@is_logged_in
def transaction():
    form = SendMoneyForm(request.form)
    balance = get_balance(session.get('username'))

    #if form is submitted
    if request.method == 'POST':
        try:
            text = form.random_text.data
            text=sha256_crypt.encrypt(form.random_text.data)
            
            #attempt to execute the transaction
        
            send_money(session.get('username'), form.username.data, form.amount.data,text)
            flash("Money Sent!", "success")
        except Exception as e:
            flash(str(e), 'danger')

        return redirect(url_for('transaction'))

    return render_template('transaction.html', balance=balance, form=form, page='transaction')

#Buy page
@app.route("/buy", methods = ['GET', 'POST'])
@is_logged_in
def buy():
    form = BuyForm(request.form)
    balance = get_balance(session.get('username'))
    if request.method == 'POST':
        #attempt to buy amount
        try:
            text = form.random_text.data
            text=sha256_crypt.encrypt(form.random_text.data)
            #print(text)
            send_money("BANK", session.get('username'), form.amount.data,text)
            flash("Purchase Successful!", "success")
        except Exception as e:
            #print(form.amount.data)
            flash(str(e), 'danger')

        return redirect(url_for('dashboard'))

    return render_template('buy.html', balance=balance, form=form, page='buy')

#logout the user. Ends current session
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash("Logout success", "success")
    return redirect(url_for('login'))

#Dashboard page
@app.route("/dashboard")
@is_logged_in
def dashboard():
    balance = get_balance(session.get('username'))
    blockchain = get_blockchain().chain
    ct = time.strftime("%I:%M %p")
    
    return render_template('dashboard.html', balance=balance, session=session, ct=ct, blockchain=blockchain, page='dashboard')

#Index page
@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html')

#mining the target block
from hashlib import sha256
import time
def SHA256(text):
    return sha256(text.encode("ascii")).hexdigest()
@app.route('/mine', methods=['GET','POST'])
@is_logged_in
def mine():
    text = SHA256("Mining")
    form = MineForm(request.form)
    if request.method=='POST':
        start = time.time()
        #flash("Mining Started")
        target_block = form.target_block.data
        max_try = int(form.max_try.data)
        target_block = SHA256(target_block )
        amount = form.amount.data
        start_block = form.start_block.data
        if start_block ==" ":
            start_block = SHA256(start_block )
        for x in range(64):
            prefix_str = '0'*int(x)
            if target_block.startswith(prefix_str):
                continue
            else:
                target_prefix = '0'*x
                break
        if start_block.startswith(prefix_str):
            flash("Yay! Successfully mined with nonce value:"+str(amount),"success")
            send_money("MINING", session.get('username'), form.amount.data,text)
            flash("Money added Successfully!", "success")
            total_time = str((time.time() - start))
            flash("Mining Ended. Mining took: "+ total_time+ " seconds","success")
            return redirect(url_for('dashboard'))
        else:
            for nonce in range(max_try):
                new_hash = SHA256(start_block)
                if new_hash.startswith(prefix_str):
                    flash("Yay! Successfully mined with nonce value:"+str(amount),"success")
                    send_money("MINING", session.get('username'), form.amount.data,text)
                    total_time = str((time.time() - start))
                    flash("Mining Ended. Mining took: "+ total_time+ " seconds","success")
                    return redirect(url_for('dashboard'))
            flash("Max trys reached, no coin was mined",'danger')
    return render_template('mine.html',form=form)
    
#Run app
if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug = True)



