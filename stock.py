import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox
from pathlib import Path    
from find_saved_datafile_path import FindSavedDatafilePath
 
import sys # เพิ่ม sys
import os
import chmodule
from create_database import CREATE_LOTS_TABLE, CREATE_DIVIDENDS_TABLE, CREATE_CAPITAL_RETURNS_TABLE # Import AppcreateDB เพื่อเรียกใช้ฟังก์ชัน

# --- (แก้ไข) Import คลาสของหน้าต่างย่อยๆ ---
from transaction import Tran_app
from dividend_return import DividendReturnApp
from stock_analyze import StockAnalyzeApp
from single_stock_anal import Single_Stock_Analyzer_app
from stock_log import StockLogApp

# --- ตรวจสอบและติดตั้ง Pillow ---
try:
    from PIL import Image, ImageTk
except ImportError:
    from PIL import Image, ImageTk

from managedatabase import Appdb # Import Appdb เพื่อเรียกใช้ฟังก์ชัน

class App(tk.Toplevel): # <-- เปลี่ยนจาก tk.Tk เป็น tk.Toplevel
    def __init__(self, parent, display_image=None, door_icon=None):
        super().__init__(parent)
        self.parent = parent
        self.title("Stock window")

         # --- (แก้ไข) รับอ็อบเจกต์รูปภาพมาโดยตรง ไม่ต้องโหลดใหม่ ---
        self.iconphoto(True, parent.icon_image) # ใช้ไอคอนเดียวกับหน้าต่างหลัก
        self.display_image = display_image
        self.door_icon = door_icon

        chmodule.ChClass.setwindowcenter(self, 500, 320)
        self.status_bar = chmodule.ChClass.status_bar("Ready", self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        


        # เรียก dialog หลังจาก window สร้างเสร็จ
        self.after(100, self.open_file_dialog)
        self._create_transaction_buttons() # สร้างปุ่มต่าง ๆ หลังจากเปิด dialog แล้ว
        self.deiconify() # แสดงหน้าต่างนี้หลังจากสร้างปุ่มต่าง ๆ เสร็จแล้ว



    def open_file_dialog(self):
        from tkinter import filedialog, messagebox
        from pathlib import Path
        from find_saved_datafile_path import FindSavedDatafilePath

        finder = FindSavedDatafilePath()

        folder_path = finder.get_pythonista_icloud_path()

        print("กำลังเปิด dialog เลือกไฟล์...")
        print(f"Debug: กำลังตรวจสอบ Path: {folder_path}")
        if not Path(folder_path).exists():
            print("Warning: Path ที่ระบุไม่มีอยู่จริง เปลี่ยนไปใช้ Directory ปัจจุบันแทน")
            folder_path = "."
        filename = filedialog.askopenfilename(
            parent=self,   # ใช้ root Tk เป็น parent
            initialdir=folder_path,
            title="เลือกไฟล์ Stock",
            filetypes=[("Stock files", "stock*.*")]
        )
        print("ผลลัพธ์ filename =", filename)

        if filename:
            self.selected_file = Path(filename)
            print("เลือกไฟล์:", self.selected_file)
        else:
            messagebox.showinfo("ยังไม่ได้เลือกไฟล์", "คุณยังไม่ได้เลือกไฟล์ฐานข้อมูล", parent=self)
            self.on_close()

    def on_close(self):
        self.parent.deiconify()
        self.destroy()



    def _create_transaction_buttons(self):
        """สร้าง Canvas และปุ่มสำหรับจัดการข้อมูลหลังจากเปิดฐานข้อมูล"""
        # --- สร้าง Frame หลักเพื่อจัดวางรูปภาพ (ซ้าย) และปุ่ม (ขวา) ---
        main_content_frame = ttk.Frame(self)
        main_content_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        # --- ส่วนรูปภาพด้านซ้าย ---
        if self.display_image:
            image_label = ttk.Label(main_content_frame, image=self.display_image)
            image_label.pack(side=tk.LEFT, padx=20, pady=10)

        # --- ส่วนปุ่มด้านขวา ---
        button_frame = ttk.Frame(main_content_frame)
        button_frame.pack(side=tk.RIGHT, padx=(10, 20), fill=tk.Y)

        # --- สร้างปุ่มต่างๆ ---
        btn_add_trans = ttk.Button(
            button_frame, text="Add Transaction",
            command=self.open_transaction_window
        )
        btn_add_dividend_return = ttk.Button(
            button_frame, text="เพิ่มข้อมูลปันผล / คืนทุน",
            command=self.open_dividend_return_window
        )
        btn_analyze_stock = ttk.Button(
            button_frame, text="วิเคราะห์ภาพรวมพอร์ต", command=self.open_stock_analyze_window
        )
        btn_analyze_individual_stock = ttk.Button(
            button_frame, text="วิเคราะห์หุ้นรายตัว", command=self.open_single_stock_analyze_window
        )
        btn_log = ttk.Button(button_frame, text="Log", command=self.open_stock_log_window)
        
        # --- จัดวางปุ่มใน Frame ---
        btn_add_trans.pack(pady=5, fill=tk.X)
        btn_add_dividend_return.pack(pady=5, fill=tk.X)
        btn_analyze_stock.pack(pady=5, fill=tk.X)
        btn_analyze_individual_stock.pack(pady=5, fill=tk.X)
        btn_log.pack(pady=5, fill=tk.X)

        # --- เพิ่มไอคอนสำหรับออกจากโปรแกรม ---
        exit_frame = ttk.Frame(button_frame)
        exit_frame.pack(side=tk.BOTTOM, pady=(0, 0)) # วางไว้ด้านล่างสุดของ button_frame

        tooltip_text = "คลิกเพื่อออกจากโปรแกรม"

        if self.door_icon:
            door_label = ttk.Label(exit_frame, image=self.door_icon, cursor="hand2")
            door_label.pack()
            door_label.bind("<Button-1>", lambda event: self.on_close())
            door_label.bind("<Enter>", lambda event: self._update_statusbar(tooltip_text))
            door_label.bind("<Leave>", lambda event: self._update_statusbar("Ready"))
        
    def _update_statusbar(self, text):
        """Internal method to update the status bar text."""
        chmodule.ChClass.status_bar(text, self)

    # --- (เพิ่ม) ฟังก์ชันสำหรับเปิดหน้าต่างย่อยๆ ---
    def open_transaction_window(self):
        trans_win = Tran_app(parent=self, db_path=self.selected_file)
        trans_win.grab_set()

    def open_stock_analyze_window(self):
        analyze_win = StockAnalyzeApp(parent=self, db_path=self.selected_file)
        analyze_win.grab_set()

    def open_single_stock_analyze_window(self):
        # (แก้ไข) สร้างเป็น Toplevel และส่งข้อมูลที่จำเป็นไปให้
        single_analyze_win = Single_Stock_Analyzer_app(parent=self,
                                                       db_path=self.selected_file,
                                                       door_icon=self.door_icon)
        single_analyze_win.grab_set()

    def open_stock_log_window(self):
        log_win = StockLogApp(parent=self, db_path=self.selected_file)
        log_win.grab_set()

    def open_dividend_return_window(self):
        div_win = DividendReturnApp(parent=self, db_path=self.selected_file)
        div_win.grab_set()
    
if __name__ == "__main__":
    app = App()
    app.mainloop()

# stock.py
