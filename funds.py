import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont, messagebox
import sys # เพิ่ม sys
import os
import chmodule # Import AppcreateDB เพื่อเรียกใช้ฟังก์ชัน
import sqlite3

# --- (แก้ไข) Import คลาสของหน้าต่างย่อยๆ ---
from transaction_for_funds import Tran_app # เปลี่ยนไปใช้ Tran_app จาก transaction_for_funds.py
from dividend_return import DividendReturnApp
from stock_analyze import StockAnalyzeApp
from single_stock_anal import Single_Stock_Analyzer_app
from stock_log import StockLogApp

# --- ตรวจสอบและติดตั้ง Pillow ---
try:
    from PIL import Image, ImageTk
except ImportError:
    from PIL import Image, ImageTk




class WaitingListDialog(tk.Toplevel):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.title("รายการรอดำเนินการ")
        self.db_path = db_path
        chmodule.ChClass.setwindowcenter(self, 600, 350)
        
        self.create_widgets()
        self.load_pending_records()
        
        self.transient(parent)
        self.grab_set()
        self.wait_window()

    def create_widgets(self):
        self.label = ttk.Label(self, text="รายการที่รอดำเนินการ", font=("Helvetica", 12, "bold"))
        self.label.pack(pady=10)

        columns = ("Type", "Symbol", "Quantity", "Price", "Date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        
        self.tree.heading("Type", text="ประเภท")
        self.tree.heading("Symbol", text="ชื่อกองทุน")
        self.tree.heading("Quantity", text="จำนวน")
        self.tree.heading("Price", text="ราคา")
        self.tree.heading("Date", text="วันที่")
        
        self.tree.column("Type", width=80, anchor="center")
        self.tree.column("Symbol", width=120, anchor="w")
        self.tree.column("Quantity", width=80, anchor="e")
        self.tree.column("Price", width=80, anchor="e")
        self.tree.column("Date", width=100, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        btn_close = ttk.Button(self, text="ปิด", command=self.destroy)
        btn_close.pack(pady=10)

    def load_pending_records(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        temp_db_manager = TempDbManager(self.db_path)

        try:
            lots_records = temp_db_manager.fetch_all("SELECT symbol, volume, price_per_unit, date FROM waiting_lots WHERE status = 'BUY_WAITING'")
            for record in lots_records:
                self.tree.insert("", tk.END, values=("ซื้อรอ", record[0], record[1], record[2], record[3]))
        except Exception as e:
            print(f"Warning: ไม่สามารถดึงข้อมูลจาก waiting_lots ได้: {e}")

        try:
            sales_records = temp_db_manager.fetch_all("SELECT symbol, volume, price_per_unit, date FROM waiting_lots WHERE status = 'SELL_WAITING'")
            for record in sales_records:
                self.tree.insert("", tk.END, values=("ขายรอ", record[0], record[1], record[2], record[3]))
        except Exception as e:
            print(f"Warning: ไม่สามารถดึงข้อมูลจาก waiting_lots ได้: {e}")

class TempDbManager:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def fetch_all(self, query):
        """สำหรับดึงข้อมูลหลายแถว"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result

    def fetch_one(self, query):
        """สำหรับดึงข้อมูลแถวเดียว"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()
        return result   

class App(tk.Toplevel): # <-- เปลี่ยนจาก tk.Tk เป็น tk.Toplevel
    def __init__(self, parent, display_image, door_icon): 
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
            filetypes=[("Stock files", "fund*.db")]
        )
        print("ผลลัพธ์ filename =", filename)

        if filename:
            self.selected_file = Path(filename)
            print("เลือกไฟล์:", self.selected_file)
        else:
            messagebox.showinfo("ยังไม่ได้เลือกไฟล์", "คุณยังไม่ได้เลือกไฟล์ฐานข้อมูล", parent=self)
            self.on_close()

    # ในคลาสของคุณใน funds.py
    def get_db_data(self, query):
        if not self.selected_file:
            return None
        
        # 1. เชื่อมต่อไปยังไฟล์ที่เลือก
        conn = sqlite3.connect(self.selected_file)
        cursor = conn.cursor()
        
        # 2. รันคำสั่ง
        cursor.execute(query)
        result = cursor.fetchone()
        
        # 3. ปิดการเชื่อมต่อ
        conn.close()
        
        return result
        

    def on_close(self):
        self.parent.deiconify() # แสดงหน้าต่างหลักอีกครั้ง
        self.destroy() # ปิดแค่หน้าต่างนี้
        

    def _check_and_display_pending_records(self):
        """ตรวจสอบรายการที่รอดำเนินการใน waiting_lots และ waiting_lots และแสดงหน้าต่าง dialog หากพบ"""
        has_pending = False
        try:
            # สมมติว่า db_manager มีเมธอด fetch_one ที่รับ SQL และคืนค่าแถวเดียว/tuple
            lots_count = self.get_db_data("SELECT COUNT(*) FROM waiting_lots")[0]
            if lots_count > 0:
                has_pending = True
        except Exception as e:
            print(f"Warning: ไม่สามารถตรวจสอบตาราง waiting_lots ได้ (ตารางอาจยังไม่มี): {e}")

        try:
            sales_count = self.get_db_data("SELECT COUNT(*) FROM waiting_lots")[0]
            if sales_count > 0:
                has_pending = True
        except Exception as e:
            print(f"Warning: ไม่สามารถตรวจสอบตาราง waiting_lots ได้ (ตารางอาจยังไม่มี): {e}")

        if has_pending:
            temp_manager = TempDbManager(self.selected_file)
            WaitingListDialog(self, temp_manager) # หน้าต่าง dialog เป็นแบบ Modal และจะบล็อกจนกว่าจะถูกปิด

    def reset_to_initial_state(self):
        """ล้างหน้าจอและวิดเจ็ตทั้งหมด กลับไปที่หน้าจอเริ่มต้น"""
        # ล้างวิดเจ็ตทั้งหมด ยกเว้น status bar
        for widget in self.winfo_children():
            if widget is self.status_bar.master:
                continue
            widget.destroy()
        
        # ล้างค่า db_path ที่เก็บไว้
        self.db_manager.db_path = None
        try:
            # ล้างไฟล์ที่เก็บบันทึกไฟล์ล่าสุด
            if os.path.exists(self.recent_db_file):
                os.remove(self.recent_db_file)
        except Exception as e:
            print(f"ไม่สามารถลบไฟล์ recent_db.txt ได้: {e}")

        self.create_widgets() # สร้างหน้าจอเริ่มต้นขึ้นมาใหม่

    def open_recent_database(self):
        """อ่านพาธจากไฟล์ config และเปิดฐานข้อมูลล่าสุด"""
        try:
            if not os.path.exists(self.recent_db_file):
                messagebox.showwarning("ไม่พบไฟล์ล่าสุด", "ยังไม่มีประวัติการเปิดไฟล์ฐานข้อมูลล่าสุด")
                return

            with open(self.recent_db_file, 'r') as f:
                db_path = f.read().strip()

            if not db_path:
                messagebox.showwarning("ไม่พบไฟล์ล่าสุด", "ประวัติการเปิดไฟล์ล่าสุดว่างเปล่า")
                return

            if not os.path.exists(db_path):
                messagebox.showerror("เกิดข้อผิดพลาด", f"ไม่พบไฟล์ฐานข้อมูลที่:\n{db_path}\nไฟล์อาจถูกย้ายหรือลบไปแล้ว")
                return

            # ตรวจสอบความถูกต้องของไฟล์ก่อนเปิด
            is_valid, error_message = self.db_manager._is_schema_valid(db_path)
            if is_valid:
                self.on_database_opened(db_path)
            else:
                messagebox.showerror("ไฟล์ไม่ถูกต้อง", f"โครงสร้างของไฟล์ '{os.path.basename(db_path)}' ไม่ถูกต้อง\n\n{error_message}")

        except Exception as e:
            messagebox.showerror("เกิดข้อผิดพลาด", f"ไม่สามารถเปิดไฟล์ล่าสุดได้: {e}")

    def create_widgets(self):
        

        # Load custom font
        self.custom_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.instruction_font = tkfont.Font(family="Helvetica", size=12) # สร้างฟอนต์ใหม่สำหรับคำแนะนำ

        # สร้าง Label แบบปกติ และจัดวางไว้ด้านบน
        self.label = ttk.Label(self, text="สวัสดีครับ  นักลงทุน", font=self.custom_font, anchor="center")
        self.label.pack(pady=(10, 5)) # เพิ่มระยะห่างด้านบนและล่าง

        # เพิ่ม Label แถวที่สองสำหรับคำแนะนำ
        self.instruction_label = ttk.Label(
            self,
            text="กรุณาเลือก เมนู การทำงานที่เมนูบาร์ เพื่อ\nสร้างไฟล์ฐานข้อมูลใหม่ หรือ เปิดฐานข้อมูลที่มีอยู่แล้วครับ",
            font=self.instruction_font,
            anchor="center",
            justify=tk.CENTER # เพิ่ม justify เพื่อจัดกึ่งกลางข้อความหลายบรรทัด
        )
        self.instruction_label.pack(pady=(0, 15)) # เพิ่มระยะห่างด้านล่างก่อนถึงปุ่ม

        # --- สร้างปุ่ม "ออกจากโปรแกรม" ที่หน้าแรก ---
        button_width = 150
        button_height = 50
        window_width = 500
        window_height = 300

        # คำนวณตำแหน่งเพื่อจัดกึ่งกลาง และห่างจากขอบล่าง 20 pixels
        x_pos = 30
        y_pos = (window_height - button_height - 20)

        tooltip_text = "คลิกเพื่อออกจากโปรแกรม"

        self.exit_button = ttk.Button(
            self,
            text="ออกจากโปรแกรม",
            command=self.on_close
        )
        self.exit_button.place(x=x_pos, y=y_pos, width=button_width, height=button_height)
        self.exit_button.bind("<Enter>", lambda event: self._update_statusbar(tooltip_text))
        self.exit_button.bind("<Leave>", lambda event: self._update_statusbar("Ready"))

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

        trans_win = Tran_app(parent=self, db_path=self.db_manager.db_path)
        trans_win.grab_set()
    

    def open_stock_analyze_window(self):
        analyze_win = StockAnalyzeApp(parent=self, db_path=self.db_manager.db_path)
        analyze_win.grab_set()

    def open_single_stock_analyze_window(self):
        # (แก้ไข) สร้างเป็น Toplevel และส่งข้อมูลที่จำเป็นไปให้
        single_analyze_win = Single_Stock_Analyzer_app(parent=self,
                                                       db_path=self.db_manager.db_path,
                                                       door_icon=self.door_icon)
        single_analyze_win.grab_set()

    def open_stock_log_window(self):
        log_win = StockLogApp(parent=self, db_path=self.db_manager.db_path)
        log_win.grab_set()

    def open_dividend_return_window(self):
        div_win = DividendReturnApp(parent=self, db_path=self.db_manager.db_path)
        div_win.grab_set()
    
if __name__ == "__main__":
    app = App()
    app.mainloop()

# stock.py
