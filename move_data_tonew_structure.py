import sqlite3
import os

def migrate_exact_data():
    # ระบุพาธไฟล์ตามที่คุณชนะต้องการ
    old_db = '/Users/chanaimac/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/stockfundios/stockUSWebullold.db'
    new_db = '/Users/chanaimac/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/stockfundios/stockUSWebullnew.db'

    if not os.path.exists(old_db):
        print(f"❌ ไม่พบไฟล์ต้นทาง: {old_db}")
        return

    try:
        # เชื่อมต่อฐานข้อมูล
        conn_old = sqlite3.connect(old_db)
        conn_new = sqlite3.connect(new_db)
        cursor_old = conn_old.cursor()
        cursor_new = conn_new.cursor()

        # รายชื่อตารางทั้งหมดที่ต้องการย้าย
        tables = ['lots', 'sales', 'dividends', 'capital_returns', 'waiting_lots']

        print("--- เริ่มการย้ายข้อมูลแบบต้นฉบับ ---")

        for table in tables:
            try:
                # 1. ดึงข้อมูลทั้งหมดจากตารางเดิม
                cursor_old.execute(f"SELECT * FROM {table}")
                rows = cursor_old.fetchall()
                
                if not rows:
                    print(f"ℹ️ ตาราง {table}: ไม่มีข้อมูลให้ย้าย")
                    continue

                # 2. ดึงรายชื่อคอลัมน์เพื่อสร้าง SQL Insert
                cursor_old.execute(f"PRAGMA table_info({table})")
                columns = [info[1] for info in cursor_old.fetchall()]
                col_names = ", ".join(columns)
                placeholders = ", ".join(["?"] * len(columns))

                # 3. ใส่ข้อมูลลงในตารางใหม่
                insert_sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                cursor_new.executemany(insert_sql, rows)
                
                conn_new.commit()
                print(f"✅ ย้ายตาราง {table} สำเร็จ: {len(rows)} รายการ")

            except sqlite3.OperationalError as e:
                print(f"⚠️ ข้ามตาราง {table}: {e}")

        print("-------------------------------")
        print("🎉 ย้ายข้อมูลเดิมเข้าไฟล์ใหม่เรียบร้อยแล้วครับ")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        conn_old.close()
        conn_new.close()

if __name__ == "__main__":
    migrate_exact_data()