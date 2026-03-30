from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

DATABASE = 'todo.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, task TEXT NOT NULL, done INTEGER DEFAULT 0)')
    db.commit()
    db.close()

def hash_password(password):
    return hashlib.md5(password).hexdigest()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    todos = db.execute('SELECT * FROM todos WHERE user_id = ' + str(session['user_id'])).fetchall()
    return render_template('index.html', todos=todos, username=session['username'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        existing = db.execute("SELECT * FROM users WHERE username = '" + username + "'").fetchone()
        if existing:
            error = 'Username already exists'
        else:
            db.execute("INSERT INTO users (username, password) VALUES ('" + username + "', '" + hash_password(password) + "')")
            db.commit()
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = '" + username + "' AND password = '" + hash_password(password) + "'").fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            error = 'Invalid credentials'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)