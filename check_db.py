import sqlite3

db_path = '/Users/chanaimac/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/stockfundios/stockUSWebull.db' # <--- เปลี่ยนเป็นชื่อไฟล์ของคุณ

def check_data():
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("--- 1. ตรวจสอบค่า NULL ในตาราง sales ---")
        # เช็คว่ามีคอลัมน์ไหนที่เป็นค่าว่าง (NULL) ในส่วนที่ต้องใช้คำนวณบ้าง
        cursor.execute("""
            SELECT 
                count(*) FILTER (WHERE lot_id IS NULL) as null_lot,
                count(*) FILTER (WHERE sell_volume IS NULL) as null_vol,
                count(*) FILTER (WHERE sell_price_per_unit IS NULL) as null_price,
                count(*) FROM sales
        """)
        res = cursor.fetchone()
        print(f"จำนวนรายการขายทั้งหมด: {res[3]} รายการ")
        print(f"พบ lot_id เป็นว่าง: {res[0]} รายการ")
        print(f"พบจำนวนขายเป็นว่าง: {res[1]} รายการ")
        print(f"พบราคาขายเป็นว่าง: {res[2]} รายการ")

        print("\n--- 2. ตรวจสอบชนิดข้อมูล (Data Type) ของ lot_id ---")
        # ดูว่า lot_id เก็บเป็นตัวเลข หรือ เก็บเป็นข้อความ (String)
        cursor.execute("SELECT lot_id, typeof(lot_id) as type FROM sales LIMIT 5")
        rows = cursor.fetchall()
        for r in rows:
            print(f"lot_id: {r['lot_id']} | Type: {r['type']}")

        print("\n--- 3. ตรวจสอบการเชื่อมโยง (Broken Links) ---")
        # ลอง Join ดูว่ามีรายการขายไหนที่หาคู่ในตาราง lots ไม่เจอ
        cursor.execute("""
            SELECT s.sale_id, s.lot_id 
            FROM sales s 
            LEFT JOIN lots l ON CAST(s.lot_id AS TEXT) = CAST(l.lot_id AS TEXT)
            WHERE l.lot_id IS NULL
        """)
        broken = cursor.fetchall()
        print(f"พบรายการขายที่หาล็อตไม่เจอ (Broken Join): {len(broken)} รายการ")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()