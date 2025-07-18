from flask import Flask, render_template, request, redirect, jsonify, Response
import sqlite3
from functools import wraps
import pycountry  # <-- импортируем

app = Flask(__name__)

def init_db():
    with sqlite3.connect('survey.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT,
                gender TEXT,
                age TEXT,
                with_children TEXT,
                source TEXT,
                travel_mode TEXT,
                days TEXT,
                accommodation TEXT,
                suggestions TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

init_db()

ADMIN_PASSWORD = 'Baurzhan'

def check_auth(password):
    return password == ADMIN_PASSWORD

def authenticate():
    return Response(
        'Требуется авторизация.', 401,
        {'WWW-Authenticate': 'Basic realm="Admin Area"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def get_countries():
    # Собираем и сортируем все страны по имени
    return sorted([country.name for country in pycountry.countries])

@app.route('/')
def index():
    countries = get_countries()
    return render_template('index.html', countries=countries)

@app.route('/submit', methods=['POST'])
def submit():
    data = {
        "country": request.form.get("country"),
        "gender": request.form.get("gender"),
        "age": request.form.get("age"),
        "with_children": request.form.get("with_children"),
        "source": request.form.get("source"),
        "travel_mode": request.form.get("travel_mode"),
        "days": request.form.get("days"),
        "accommodation": request.form.get("accommodation"),
        "suggestions": request.form.get("suggestions")
    }
    with sqlite3.connect('survey.db') as conn:
        conn.execute('''
            INSERT INTO responses (
                country, gender, age, with_children, source,
                travel_mode, days, accommodation, suggestions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data["country"], data["gender"], data["age"], data["with_children"],
            data["source"], data["travel_mode"], data["days"], data["accommodation"],
            data["suggestions"]
        ))
    return redirect('/thank_you')

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/admin')
@requires_auth
def admin():
    return render_template('admin.html')

@app.route('/results')
@requires_auth
def results():
    with sqlite3.connect('survey.db') as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM responses ORDER BY submitted_at DESC').fetchall()
        return jsonify([dict(row) for row in rows])

if __name__ == '__main__':
    app.run(debug=True)
