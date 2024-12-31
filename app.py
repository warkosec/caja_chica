from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Clave secreta para las sesiones

# Función para inicializar la base de datos
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY,
                        description TEXT,
                        amount REAL,
                        type TEXT,
                        date_time TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS openings (
                        id INTEGER PRIMARY KEY,
                        cash REAL,
                        checks REAL,
                        vouchers REAL,
                        date_time TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS closings (
                        id INTEGER PRIMARY KEY,
                        cash REAL,
                        checks REAL,
                        vouchers REAL,
                        date_time TEXT)''')
    conn.commit()
    conn.close()

# Ruta para la página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'Caja1' and password == 'Taller2024':
            session['logged_in'] = True
            return redirect(url_for('apertura'))
        else:
            error = 'Usuario o contraseña incorrecta'
            return render_template('login.html', error=error)
    return render_template('login.html')

# Ruta para la apertura de caja
@app.route('/apertura', methods=['GET', 'POST'])
def apertura():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        cash = float(request.form['cash'])
        checks = float(request.form['checks'])
        vouchers = float(request.form['vouchers'])
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO openings (cash, checks, vouchers, date_time) VALUES (?, ?, ?, ?)",
                       (cash, checks, vouchers, date_time))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('opening.html')

# Ruta para el cierre de caja
@app.route('/cierre', methods=['GET', 'POST'])
def cierre():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        cash = float(request.form['cash'])
        checks = float(request.form['checks'])
        vouchers = float(request.form['vouchers'])
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO closings (cash, checks, vouchers, date_time) VALUES (?, ?, ?, ?)",
                       (cash, checks, vouchers, date_time))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('closing.html')

# Ruta para la página principal
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM openings WHERE date_time LIKE ?", (today + "%",))
    opening = cursor.fetchone()

    if not opening:
        return redirect(url_for('apertura'))

    cursor.execute("SELECT * FROM transactions WHERE date_time LIKE ?", (today + "%",))
    transactions = cursor.fetchall()
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE date_time LIKE ? AND type='Ingreso'", (today + "%",))
    total_ingresos = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE date_time LIKE ? AND type='Egreso'", (today + "%",))
    total_egresos = cursor.fetchone()[0] or 0
    
    initial_cash = opening[1]  # Dinero en efectivo de la apertura de caja

    # Balance actual considerando los valores de apertura y las transacciones del día
    balance = initial_cash + total_ingresos - total_egresos
    
    conn.close()
    return render_template('index.html', transactions=transactions, total_ingresos=total_ingresos, total_egresos=total_egresos, balance=balance, initial_cash=initial_cash)

# Ruta para agregar una transacción
@app.route('/add', methods=['POST'])
def add_transaction():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    description = request.form['description']
    amount = float(request.form['amount'])
    trans_type = request.form['type']
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (description, amount, type, date_time) VALUES (?, ?, ?, ?)",
                   (description, amount, trans_type, date_time))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Ruta para reportes
@app.route('/reporte', methods=['GET', 'POST'])
def reporte():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    transactions = []
    total_ingresos = 0
    total_egresos = 0
    date = ''
    if request.method == 'POST':
        date = request.form['date']
        start_date = date + " 00:00:00"
        end_date = date + " 23:59:59"
        
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM closings WHERE date_time BETWEEN ? AND ?", (start_date, end_date))
        closing = cursor.fetchone()

        if closing:
            cursor.execute("SELECT * FROM transactions WHERE date_time BETWEEN ? AND ?", (start_date, end_date))
            transactions = cursor.fetchall()

            cursor.execute("SELECT SUM(amount) FROM transactions WHERE date_time BETWEEN ? AND ? AND type='Ingreso'", (start_date, end_date))
            total_ingresos = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(amount) FROM transactions WHERE date_time BETWEEN ? AND ? AND type='Egreso'", (start_date, end_date))
            total_egresos = cursor.fetchone()[0] or 0

        conn.close()
    
    return render_template('reporte.html', transactions=transactions, date=date, total_ingresos=total_ingresos, total_egresos=total_egresos)

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Inicializar la base de datos
init_db()

if __name__ == '__main__':
    app.run(debug=True)