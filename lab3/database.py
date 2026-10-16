"""SQLite storage for SmartShop Assistant laboratory 2."""
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(os.environ.get('DATABASE_PATH', str(Path(__file__).resolve().parent / 'smartshop.db')))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SEED_PRODUCTS = [
    (1, 'Футболка Basic', 'Одежда', 1500, 15, 'Хлопковая футболка на каждый день.'),
    (2, 'Худи Comfort', 'Одежда', 3500, 8, 'Тёплое худи свободного кроя.'),
    (3, 'Кроссовки Active', 'Обувь', 5900, 12, 'Удобные кроссовки для прогулок.'),
    (4, 'Рюкзак City', 'Аксессуары', 2500, 6, 'Городской рюкзак на 20 литров.'),
    (5, 'Кепка Sport', 'Аксессуары', 900, 20, 'Лёгкая регулируемая кепка.'),
    (6, 'Ботинки Winter', 'Обувь', 7200, 4, 'Утеплённые зимние ботинки.'),
]


def connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    return connection


def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL,
            category TEXT NOT NULL, price INTEGER NOT NULL CHECK(price >= 0),
            stock INTEGER NOT NULL CHECK(stock >= 0), description TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY, first_name TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
            PRIMARY KEY(user_id, product_id),
            FOREIGN KEY(user_id) REFERENCES users(telegram_id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS cart (
            user_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            PRIMARY KEY(user_id, product_id),
            FOREIGN KEY(user_id) REFERENCES users(telegram_id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, total INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(telegram_id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            order_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL, unit_price INTEGER NOT NULL,
            PRIMARY KEY(order_id, product_id),
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        ''')
        db.executemany('''INSERT OR IGNORE INTO products
          (id, name, category, price, stock, description)
          VALUES (?, ?, ?, ?, ?, ?)''', SEED_PRODUCTS)


def ensure_user(user_id, first_name=''):
    with connect() as db:
        db.execute('INSERT OR IGNORE INTO users(telegram_id,first_name) VALUES (?,?)', (user_id, first_name))


def products(category=None, term=None):
    query = 'SELECT * FROM products WHERE 1=1'
    params = []
    if category:
        query += ' AND category=?'
        params.append(category)
    if term:
        query += ' AND (lower(name) LIKE ? OR lower(description) LIKE ?)'
        params += ['%' + term.lower() + '%'] * 2
    query += ' ORDER BY id'
    with connect() as db:
        return [dict(row) for row in db.execute(query, params)]


def product(product_id):
    with connect() as db:
        row = db.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
        return dict(row) if row else None


def favorites(user_id):
    with connect() as db:
        return [dict(row) for row in db.execute('''SELECT p.* FROM favorites f
         JOIN products p ON p.id=f.product_id WHERE f.user_id=? ORDER BY p.id''', (user_id,))]


def toggle_favorite(user_id, product_id):
    with connect() as db:
        found = db.execute('SELECT 1 FROM favorites WHERE user_id=? AND product_id=?', (user_id, product_id)).fetchone()
        if found:
            db.execute('DELETE FROM favorites WHERE user_id=? AND product_id=?', (user_id, product_id))
            return False
        db.execute('INSERT INTO favorites(user_id,product_id) VALUES (?,?)', (user_id, product_id))
        return True


def cart_items(user_id):
    with connect() as db:
        return [dict(row) for row in db.execute('''SELECT p.*, c.quantity FROM cart c
          JOIN products p ON p.id=c.product_id WHERE c.user_id=? ORDER BY p.id''', (user_id,))]


def add_to_cart(user_id, product_id):
    with connect() as db:
        row = db.execute('''SELECT p.stock, COALESCE(c.quantity,0) AS qty FROM products p
          LEFT JOIN cart c ON c.product_id=p.id AND c.user_id=? WHERE p.id=?''', (user_id, product_id)).fetchone()
        if row is None:
            return 'missing'
        if row['qty'] >= row['stock']:
            return 'stock'
        db.execute('''INSERT INTO cart(user_id,product_id,quantity) VALUES (?,?,1)
          ON CONFLICT(user_id,product_id) DO UPDATE SET quantity=quantity+1''', (user_id, product_id))
        return 'ok'


def remove_from_cart(user_id, product_id):
    with connect() as db:
        row = db.execute('SELECT quantity FROM cart WHERE user_id=? AND product_id=?', (user_id, product_id)).fetchone()
        if not row:
            return False
        if row['quantity'] <= 1:
            db.execute('DELETE FROM cart WHERE user_id=? AND product_id=?', (user_id,product_id))
        else:
            db.execute('UPDATE cart SET quantity=quantity-1 WHERE user_id=? AND product_id=?', (user_id,product_id))
        return True


def clear_cart(user_id):
    with connect() as db:
        db.execute('DELETE FROM cart WHERE user_id=?', (user_id,))


def place_order(user_id):
    with connect() as db:
        items = db.execute('''SELECT c.product_id,c.quantity,p.price,p.stock FROM cart c
         JOIN products p ON p.id=c.product_id WHERE c.user_id=?''', (user_id,)).fetchall()
        if not items:
            return None
        if any(item['quantity'] > item['stock'] for item in items):
            raise ValueError('Недостаточно товаров на складе')
        total = sum(item['quantity'] * item['price'] for item in items)
        cursor = db.execute('INSERT INTO orders(user_id,total) VALUES (?,?)', (user_id,total))
        order_id = cursor.lastrowid
        for item in items:
            db.execute('''INSERT INTO order_items(order_id,product_id,quantity,unit_price)
              VALUES (?,?,?,?)''', (order_id,item['product_id'],item['quantity'],item['price']))
            db.execute('UPDATE products SET stock=stock-? WHERE id=?', (item['quantity'],item['product_id']))
        db.execute('DELETE FROM cart WHERE user_id=?', (user_id,))
        return order_id, total


def orders(user_id):
    with connect() as db:
        return [dict(row) for row in db.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10', (user_id,))]
