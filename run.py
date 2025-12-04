from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'roma_aslan_god_2025'
bcrypt = Bcrypt(app)

# Контекст для шаблонов
@app.context_processor
def inject_globals():
    return {
        'request': request,
        'session': session
    }

# Корзина в сессии
@app.before_request
def init_cart():
    if 'cart' not in session:
        session['cart'] = []

# Подключение к БД
def get_db():
    try:
        return psycopg2.connect(host="localhost", database="praktika", user="postgres", password="")
    except:
        return psycopg2.connect(host="localhost", database="praktika", user="postgres", password="123")

# Инициализация БД и создание админа
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user'
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price NUMERIC(10,2),
            image VARCHAR(255)
        )
    ''')
    # Создаём админа
    cur.execute("SELECT * FROM users WHERE email='roma@aslan.kz'")
    if not cur.fetchone():
        admin_hash = bcrypt.generate_password_hash("admin123").decode('utf-8')
        cur.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES ('roma','roma@aslan.kz', %s,'admin')",
            (admin_hash,))
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.context_processor
def inject_user():
    return dict(
        logged_in='user_id' in session,
        username=session.get('username'),
        is_admin=session.get('role') == 'admin'
    )

# Главная
@app.route('/')
def index():
    return render_template('mainmenu.html')

# Каталог
@app.route('/catalog')
def catalog():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, description, image FROM products ORDER BY id")
    products = cur.fetchall()
    cur.close()
    conn.close()
    product_list = []
    for p in products:
        product_list.append({
            'id': p[0],
            'name': p[1],
            'price': p[2],
            'description': p[3],
            'image': p[4] or '/static/images/no-photo.jpg'
        })
    return render_template('catalog.html', products=product_list)

# Добавление в корзину
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart = session.get('cart', [])
    cart.append(product_id)
    session['cart'] = cart
    session.modified = True
    flash("Товар добавлен в корзину!")
    return redirect('/catalog')

# Корзина
@app.route('/cart')
def cart():
    cart_ids = session.get('cart', [])
    conn = get_db()
    cur = conn.cursor()
    cart_items = []
    total = 0
    for pid in cart_ids:
        cur.execute("SELECT id, name, description, price, image FROM products WHERE id=%s", (pid,))
        p = cur.fetchone()
        if p:
            cart_items.append({
                'id': p[0],
                'name': p[1],
                'description': p[2],
                'price': p[3],
                'image': p[4] or '/static/images/no-photo.jpg'
            })
            total += float(p[3])
    cur.close()
    conn.close()
    return render_template('cart.html', cart_items=cart_items, total=total)

# Удаление из корзины
@app.route('/remove/<int:pid>', methods=['POST'])
def remove(pid):
    cart = session.get('cart', [])
    if pid in cart:
        cart.remove(pid)
    session['cart'] = cart
    session.modified = True
    flash("Товар удалён из корзины")
    return redirect('/cart')

# Контакты
@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

# Регистрация
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'].lower()
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username,email,password_hash,role) VALUES (%s,%s,%s,'user')",
                        (username,email,password))
            conn.commit()
            flash("Регистрация успешна! Теперь войдите")
            return redirect('/login')
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Этот email уже занят")
        finally:
            cur.close()
            conn.close()
    return render_template('register.html')

# Логин
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash, role FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and bcrypt.check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            flash(f"Привет, {user[1]}!")
            return redirect('/')
        flash("Неправильный email или пароль")
    return render_template('login.html')

# Админка
@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        flash("Только для админа")
        return redirect('/')
    return render_template('admin.html')

# Бэкап
@app.route('/backup')
def backup():
    if session.get('role') != 'admin':
        return redirect('/')
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backups/backup_{timestamp}.sql"
    os.makedirs("backups", exist_ok=True)
    os.system(f'pg_dump -U postgres praktika > "{filename}"')
    flash(f"Бэкап создан: {filename}")
    return redirect('/admin')

# Логаут
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- Checkout (оплата) ---
@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if request.method == 'POST':
        flash("Оплата принята! Спасибо за заказ.")
        session['cart'] = []
        session.modified = True
        return redirect('/')
    return render_template('checkout.html')

if __name__ == '__main__':
    app.run(debug=True)
