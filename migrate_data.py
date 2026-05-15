import sqlite3
import os

def migrate_data(source_db_path, dest_db_path):
    """
    คัดลอกข้อมูลจากฐานข้อมูลต้นทางไปยังฐานข้อมูลปลายทาง
    โดยที่ฐานข้อมูลปลายทางต้องมีโครงสร้าง (schema) ที่เหมือนกันและว่างเปล่า

    :param source_db_path: ที่อยู่ของไฟล์ฐานข้อมูลต้นทาง (มีข้อมูล)
    :param dest_db_path: ที่อยู่ของไฟล์ฐานข้อมูลปลายทาง (ว่างเปล่า)
    """
    # --- 1. ตรวจสอบว่าไฟล์ทั้งสองมีอยู่จริง ---
    if not os.path.exists(source_db_path):
        print(f"!!! ข้อผิดพลาด: ไม่พบไฟล์ฐานข้อมูลต้นทางที่ '{source_db_path}'")
        return

    if not os.path.exists(dest_db_path):
        print(f"!!! ข้อผิดพลาด: ไม่พบไฟล์ฐานข้อมูลปลายทางที่ '{dest_db_path}'")
        return

    print(f"--- เริ่มกระบวนการย้ายข้อมูลจาก '{source_db_path}' ไปยัง '{dest_db_path}' ---")

    try:
        # --- 2. เชื่อมต่อกับฐานข้อมูลทั้งสอง ---
        source_conn = sqlite3.connect(source_db_path)
        source_cursor = source_conn.cursor()

        dest_conn = sqlite3.connect(dest_db_path)
        dest_cursor = dest_conn.cursor()

        # --- 3. กำหนดลำดับของตาราง (สำคัญมากสำหรับ Foreign Keys) ---
        # ตาราง `lots` ต้องมาก่อน เพราะตารางอื่นอ้างอิงถึง
        tables_in_order = ['lots', 'dividends', 'capital_returns']

        # --- 4. วนลูปเพื่อคัดลอกข้อมูลในแต่ละตาราง ---
        for table_name in tables_in_order:
            print(f"    - กำลังอ่านข้อมูลจากตาราง '{table_name}'...")
            
            # ดึงรายชื่อคอลัมน์จากตารางต้นทาง
            source_cursor.execute(f"PRAGMA table_info({table_name})")
            source_columns = [col[1] for col in source_cursor.fetchall()]
            source_columns_str = ", ".join([f'"{col}"' for col in source_columns])

            # ดึงรายชื่อคอลัมน์จากตารางปลายทาง
            dest_cursor.execute(f"PRAGMA table_info({table_name})")
            dest_columns = [col[1] for col in dest_cursor.fetchall()]

            # หาคอลัมน์ที่มีร่วมกัน (เผื่อกรณีโครงสร้างต่างกัน)
            common_columns = [col for col in source_columns if col in dest_columns]
            common_columns_str = ", ".join([f'"{col}"' for col in common_columns])

            # ดึงข้อมูลเฉพาะคอลัมน์ที่มีร่วมกันจากตารางต้นทาง
            source_cursor.execute(f"SELECT {common_columns_str} FROM {table_name}")
            all_data = source_cursor.fetchall()

            if not all_data:
                print(f"      > ไม่พบข้อมูลในตาราง '{table_name}', ข้ามไป...")
                continue

            # สร้าง placeholders ตามจำนวนคอลัมน์ที่มีร่วมกัน
            column_count = len(common_columns)
            placeholders = ", ".join(["?"] * column_count)
            
            # สร้างคำสั่ง SQL สำหรับเพิ่มข้อมูล
            insert_sql = f"INSERT INTO {table_name} ({common_columns_str}) VALUES ({placeholders})"

            print(f"      > พบ {len(all_data)} แถว, กำลังเขียนลงในฐานข้อมูลปลายทาง...")
            
            # เพิ่มข้อมูลทั้งหมดลงในตารางปลายทางในครั้งเดียว
            dest_cursor.executemany(insert_sql, all_data)
            print(f"      > เขียนข้อมูลลงตาราง '{table_name}' สำเร็จ")

        # --- 5. บันทึกการเปลี่ยนแปลงและปิดการเชื่อมต่อ ---
        dest_conn.commit()
        print("\n*** การย้ายข้อมูลเสร็จสมบูรณ์! ***")

    except sqlite3.Error as e:
        print(f"\n!!! เกิดข้อผิดพลาดเกี่ยวกับ SQLite: {e}")
        if 'dest_conn' in locals():
            dest_conn.rollback() # ย้อนกลับการเปลี่ยนแปลงหากเกิดข้อผิดพลาด
    finally:
        if 'source_conn' in locals() and source_conn:
            source_conn.close()
        if 'dest_conn' in locals() and dest_conn:
            dest_conn.close()
        print("--- ปิดการเชื่อมต่อฐานข้อมูลทั้งหมดแล้ว ---")

if __name__ == '__main__':
    # ระบุไฟล์ต้นทางและไฟล์ปลายทางที่นี่
    migrate_data('chstock.db', 'chstock2.db')
