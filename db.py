import sqlite3

DB_FILE = "mapping.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_mapping (
            alibaba_id TEXT PRIMARY KEY,
            shopify_id TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_shopify_id(alibaba_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT shopify_id FROM product_mapping WHERE alibaba_id=?", (str(alibaba_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def save_mapping(alibaba_id, shopify_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO product_mapping (alibaba_id, shopify_id) VALUES (?, ?)", (str(alibaba_id), str(shopify_id)))
    conn.commit()
    conn.close()