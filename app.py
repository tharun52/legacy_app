import os
import sqlite3
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, g

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production')

# Database path configurable via env var — supports volume mounts in containers
DATABASE = os.environ.get('DATABASE_PATH', '/app/data/todo.db')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        'CREATE TABLE IF NOT EXISTS users '
        '(id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'username TEXT NOT NULL, password TEXT NOT NULL)'
    )
    db.execute(
        'CREATE TABLE IF NOT EXISTS todos '
        '(id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'user_id INTEGER NOT NULL, task TEXT NOT NULL, done INTEGER DEFAULT 0)'
    )
    db.commit()


def hash_password(password):
    # Python 3: encode str -> bytes before hashing
    return hashlib.md5(password.encode('utf-8')).hexdigest()


# ── Initialize DB at startup ──────────────────────────────────────────────────
# Called at module level so it runs whether started via Gunicorn or directly.
# CREATE TABLE IF NOT EXISTS is idempotent — safe to call every startup.
with app.app_context():
    init_db()


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    todos = db.execute(
        'SELECT * FROM todos WHERE user_id = ?',
        (session['user_id'],)
    ).fetchall()
    return render_template('index.html', todos=todos, username=session['username'])


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        existing = db.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        if existing:
            error = 'Username already exists'
        else:
            db.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, hash_password(password))
            )
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
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, hash_password(password))
        ).fetchone()
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
    return redirect(url_for('login'))


@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    task = request.form.get('task', '').strip()
    if task:
        db = get_db()
        db.execute(
            'INSERT INTO todos (user_id, task) VALUES (?, ?)',
            (session['user_id'], task)
        )
        db.commit()
    return redirect(url_for('index'))


@app.route('/complete/<int:todo_id>')
def complete(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    db.execute(
        'UPDATE todos SET done = 1 WHERE id = ? AND user_id = ?',
        (todo_id, session['user_id'])
    )
    db.commit()
    return redirect(url_for('index'))


@app.route('/delete/<int:todo_id>')
def delete(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    db.execute(
        'DELETE FROM todos WHERE id = ? AND user_id = ?',
        (todo_id, session['user_id'])
    )
    db.commit()
    return redirect(url_for('index'))


@app.route('/health')
def health():
    """Health check endpoint for Docker and ALB."""
    try:
        db = get_db()
        db.execute('SELECT 1')
        return {'status': 'healthy'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
