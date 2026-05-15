import sqlite3

# แนะนำให้เปลี่ยนชื่อไฟล์ตรงนี้เป็นชื่อใหม่ (เช่น fundc4.db) เพื่อเริ่มใช้โครงสร้างใหม่ที่ถูกต้องครับ
DB_FILE = "name.db" 

CREATE_LOTS_TABLE = """
CREATE TABLE IF NOT EXISTS lots (
    lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    lot_number TEXT,        -- ตัวเชื่อมหลัก (String)
    status TEXT DEFAULT 'OPEN',
    buy_date DATE NOT NULL,
    buy_volume INTEGER NOT NULL,
    buy_price_per_unit REAL NOT NULL,
    buy_commission REAL,
    remaining_volume INTEGER
);
"""

CREATE_DIVIDENDS_TABLE = """
CREATE TABLE IF NOT EXISTS dividends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL,    -- แก้เป็น TEXT เพื่อรองรับ lot_number (String)
    payment_date DATE NOT NULL,
    amount REAL NOT NULL,
    tax REAL
);
"""

CREATE_CAPITAL_RETURNS_TABLE = """
CREATE TABLE IF NOT EXISTS capital_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL,    -- แก้เป็น TEXT เพื่อรองรับ lot_number (String)
    payment_date DATE NOT NULL,
    amount REAL NOT NULL
);
"""

CREATE_SALES_TABLE = """
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL,    -- แก้เป็น TEXT เพื่อรองรับ lot_number (String)
    sell_date DATE NOT NULL,
    sell_volume INTEGER NOT NULL,
    sell_price_per_unit REAL NOT NULL,
    sell_commission REAL
);
"""

CREATE_WAITING_LOTS_TABLE = """
CREATE TABLE IF NOT EXISTS waiting_lots (
    lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    lot_number TEXT,
    status TEXT,
    date DATE NOT NULL,
    volume INTEGER NOT NULL,
    price_per_unit REAL NOT NULL,
    amount REAL,
    remaining_volume INTEGER
);
"""

def create_database():
    """Connects to the database and creates tables with corrected String types."""
    try:
        print(f"Connecting to database '{DB_FILE}'...")
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            print("Creating 'lots' table...")
            cursor.execute(CREATE_LOTS_TABLE)

            print("Creating 'dividends' table...")
            cursor.execute(CREATE_DIVIDENDS_TABLE)

            print("Creating 'capital_returns' table...")
            cursor.execute(CREATE_CAPITAL_RETURNS_TABLE)
            
            print("Creating 'sales' table...")
            cursor.execute(CREATE_SALES_TABLE)

            print("Creating 'waiting_lots' table...")
            cursor.execute(CREATE_WAITING_LOTS_TABLE)

            print("Tables created successfully with TEXT lot_id.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    create_database()