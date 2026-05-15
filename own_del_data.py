import tkinter as tk
from tkinter import messagebox
import sqlite3
import os    
import chmodule
import subprocess
DB_PATH = 'fund01.db' # กำหนดไฟล์ฐานข้อมูลที่ต้องการใช้

class Delapp (tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Show Lot Data")
        self.geometry("300x150")
        chmodule.ChClass.setwindowcenter(self, 300, 150)

        self.label = tk.Label(self, text="Enter lot_id to Show:")
        self.label.pack(pady=10)
        
        self.lot_id_entry = tk.Entry(self)
        self.lot_id_entry.pack(pady=5)
        
        self.show_button = tk.Button(self, text="Show Data", command=self.show_data)
        self.show_button.pack(pady=10)

    def show_data(self):
        lot_id = self.lot_id_entry.get().strip()
        
        if not lot_id:
            messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณาใส่ lot_id", parent=self)
            return
        
        try:
            # ใช้ with statement เพื่อจัดการการเชื่อมต่อและปิดโดยอัตโนมัติ
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                # แก้ไข: คิวรีจากตาราง lots และเลือกคอลัมน์ที่ต้องการ
                cursor.execute("SELECT * FROM waiting_lots WHERE lot_id=?", (lot_id,))
                lot_data = cursor.fetchone()
            
            if lot_data:
                # สร้างข้อความเพื่อแสดงผล
                lot_info = (f"Lot id: {lot_data[0]}\n"
                            f"Symbol: {lot_data[1]}\n"
                            f"Lot Number: {lot_data[2]}\n"
                            f"Status: {lot_data[3]}")
                
                # เปลี่ยนเป็น askokcancel เพื่อถามยืนยัน
                confirm = messagebox.askokcancel(
                    "ยืนยันการลบข้อมูล",
                    f"คุณต้องการลบข้อมูลนี้ใช่หรือไม่?\n\n{lot_info}",
                    parent=self
                )

                # ถ้าผู้ใช้กด "ตกลง" (confirm จะเป็น True) ให้เรียกใช้ฟังก์ชัน delete_lot
                if confirm:
                    self.delete_lot(lot_id)
            else:
                messagebox.showerror("ไม่พบข้อมูล", f"ไม่พบข้อมูลสำหรับ lot_id '{lot_id}'", parent=self)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {e}", parent=self)
        
    def delete_lot(self, lot_id):
        """ฟังก์ชันสำหรับลบข้อมูล Lot ID ที่ระบุ"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM waiting_lots WHERE lot_id = ?", (lot_id,))
            messagebox.showinfo("สำเร็จ", f"ลบข้อมูล Lot ID: {lot_id} เรียบร้อยแล้ว", parent=self)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการลบข้อมูล: {e}", parent=self)
    

if __name__ == "__main__":
    app = Delapp()
    app.mainloop()