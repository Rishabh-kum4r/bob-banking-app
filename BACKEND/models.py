from werkzeug.security import generate_password_hash
from database import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            balance REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')

    # Seed data — only inserted when the table is empty
    cursor.execute('SELECT COUNT(*) FROM customers')
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash('password123')
        cursor.execute(
            'INSERT INTO customers (username, password_hash) VALUES (?, ?)',
            ('admin', password_hash)
        )
        customer_id = cursor.lastrowid
        cursor.execute(
            'INSERT INTO accounts (customer_id, balance) VALUES (?, ?)',
            (customer_id, 1000.00)
        )

    conn.commit()
    conn.close()
