import sqlite3
from tkinter import messagebox


DB_PATH = 'fund01.db' # ก



try:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE  FROM dividends")
        cursor.execute("DELETE FROM capital_returns")
        messagebox.showinfo("สำเร็จ", f"ลบข้อมูล dividend and capital return สำหรับ Lot ID: เรียบร้อยแล้ว")
except sqlite3.Error as e:
    messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการลบข้อมูล: {e}")