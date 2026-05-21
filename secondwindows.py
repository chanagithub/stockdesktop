import tkinter as tk
from tkinter import filedialog

class SecondWindow:
    def __init__(self, master):
        self.master = master  # เก็บ root จาก begin.py ไว้
        self.window = tk.Toplevel(master)  # สร้างหน้าต่างใหม่
        self.window.title("Second Window")
        self.window.geometry("300x200")

        # ปุ่มเลือกไฟล์
        btn_select = tk.Button(self.window, text="เลือกไฟล์", command=self.select_file)
        btn_select.pack(pady=20)

        # ปุ่มออก
        btn_exit = tk.Button(self.window, text="ออก", command=self.close_window)
        btn_exit.pack(pady=20)

    def select_file(self):
        # ใช้หน้าต่าง self.window เป็น parent ให้ filedialog
        filename = filedialog.askopenfilename(parent=self.window, title="เลือกไฟล์")
        if filename:
            print("Selected file:", filename)
        else:
            print("No file selected")

    def close_window(self):
        self.window.destroy()  # ปิดหน้าต่างที่สอง
        self.master.deiconify() # แสดงหน้าต่าง begin.py กลับมาอีกครั้ง