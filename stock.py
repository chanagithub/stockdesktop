import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont, messagebox
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
    def __init__(self, parent, display_image, door_icon, db_manager): # <-- เพิ่ม db_manager
        super().__init__(parent) # <-- ส่ง parent ไปให้ super class
        self.parent = parent # เก็บ parent ไว้
        self.withdraw() 
        self.title("Stock window")
        self.recent_db_file = chmodule.ChClass.get_resource_path('recent_db.txt')

        # --- (แก้ไข) รับอ็อบเจกต์รูปภาพมาโดยตรง ไม่ต้องโหลดใหม่ ---
        self.iconphoto(True, parent.icon_image) # ใช้ไอคอนเดียวกับหน้าต่างหลัก
        self.display_image = display_image
        self.door_icon = door_icon

        # --- (แก้ไข) รับ db_manager มาจาก main.py ---
        self.db_manager = db_manager
        self.db_manager.on_open_success_callback = self.on_database_opened # ตั้งค่า callback ใหม่ทุกครั้ง
        chmodule.ChClass.setwindowcenter(self, 500, 400)
        self.status_bar = chmodule.ChClass.status_bar("Ready", self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.create_Menubar()

        # เริ่มต้นด้วยหน้าจอเลือกการทำงานเสมอ (ไม่เปิดไฟล์ล่าสุดอัตโนมัติ)
        self.create_widgets()

        self.deiconify() # แสดงหน้าต่างนี้หลังจากสร้างปุ่มต่าง ๆ เสร็จแล้ว
        # เมื่อหน้าต่างหลักนี้ปิด ให้ปิดหน้าต่าง db_manager ที่ซ่อนอยู่ด้วย
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # --- เพิ่มคีย์ลัด (Shortcut) ---
        self.bind("<Control-r>", lambda event: self.open_recent_database())

    def on_close(self):
        self.parent.deiconify() # แสดงหน้าต่างหลักอีกครั้ง
        self.destroy() # ปิดแค่หน้าต่างนี้

    def create_Menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        # --- Menu "การทำงาน" ---
        # แก้ไข: แยก command ออกมาเป็นฟังก์ชันเพื่อเพิ่ม logic การตรวจสอบ
        work_menu = tk.Menu(menubar, tearoff=0)
        work_menu.add_command(label="เปิด ไฟล์ฐานข้อมูลล่าสุด", command=self.open_recent_database, accelerator="Ctrl+R")
        work_menu.add_command(label="สร้างฐานข้อมูลใหม่", command=self._prompt_create_new_db)
        work_menu.add_command(label="เปิดไฟล์ฐานข้อมูล", command=self._prompt_open_db)
        work_menu.add_separator()
        work_menu.add_command(label="ปิดโปรแกรม", command=self.on_close) 
        menubar.add_cascade(label="การทำงาน", menu=work_menu)

    def _confirm_and_reset(self, action_name):
        """ถามยืนยันผู้ใช้ก่อนรีเซ็ตหน้าจอ หากมีฐานข้อมูลเปิดอยู่"""
        # ตรวจสอบว่ามี db_path อยู่หรือไม่ (แสดงว่ามีไฟล์เปิดอยู่)
        if hasattr(self.db_manager, 'db_path') and self.db_manager.db_path:
            msg = f"คุณกำลังเปิดฐานข้อมูล '{os.path.basename(self.db_manager.db_path)}' อยู่\n\n" \
                  f"การ{action_name}จะปิดไฟล์ปัจจุบันและกลับสู่หน้าจอเริ่มต้น\n" \
                  "คุณต้องการดำเนินการต่อหรือไม่?"
            if not messagebox.askyesno("ยืนยันการดำเนินการ", msg, parent=self):
                return False # ผู้ใช้ยกเลิก
        
        # รีเซ็ตหน้าจอให้กลับไปเหมือนตอนเริ่มต้น
        self.reset_to_initial_state()
        return True

    def _prompt_create_new_db(self):
        if self._confirm_and_reset("สร้างฐานข้อมูลใหม่"):
            self.create_stock_database()

    def _prompt_open_db(self):
        if self._confirm_and_reset("เปิดไฟล์ฐานข้อมูล"):
            self.db_manager.open_database("stock")

    def create_stock_database(self):
        """
        แก้ไข: เรียกใช้ create_database และส่ง path ของไฟล์ที่สร้างใหม่
        กลับมาที่ on_database_opened เพื่อจัดการหน้าต่างอย่างถูกต้อง
        """
        new_db_path = self.db_manager.create_database("stock")
        if new_db_path: # ตรวจสอบว่าผู้ใช้ไม่ได้กดยกเลิก
            self.on_database_opened(new_db_path)
        
    def on_database_opened(self, db_path):
        """Callback function ที่จะถูกเรียกโดย Appdb เมื่อเปิดไฟล์สำเร็จ"""
        self.db_manager.db_path = db_path # <--- จุดแก้ไขสำคัญ: เก็บ path ไว้ใน db_manager
        # --- บันทึกไฟล์ที่เปิดล่าสุด ---
        try:
            with open(self.recent_db_file, 'w') as f:
                f.write(db_path)
        except IOError as e:
            print(f"ไม่สามารถบันทึกไฟล์ล่าสุดได้: {e}")
        import os

        # ล้าง widget เก่าของหน้าจอเริ่มต้น (ถ้ามี)
        # ใช้ hasattr เพื่อตรวจสอบว่า widget ถูกสร้างขึ้นแล้วหรือยัง
        if hasattr(self, 'label') and self.label.winfo_exists():
            self.label.pack_forget()
        if hasattr(self, 'instruction_label') and self.instruction_label.winfo_exists():
            self.instruction_label.pack_forget()
        if hasattr(self, 'exit_button') and self.exit_button.winfo_exists():
            self.exit_button.place_forget()

        # ล้าง widget เก่าทั้งหมดใน self เพื่อเตรียมสร้างหน้าใหม่ (ยกเว้น menubar และ statusbar)
        # แก้ไข: ตรวจสอบให้รัดกุมขึ้น เพื่อไม่ให้ลบ status_bar.master (Frame) และ menubar
        for widget in self.winfo_children():
            if widget is self.status_bar.master: # ถ้าเป็น Frame ของ status bar ให้ข้ามไป
                continue
            if not isinstance(widget, tk.Menu): # ไม่ลบ Menu bar
                widget.destroy()

        # --- (เพิ่ม) Label แสดงชื่อไฟล์ที่กำลังเปิด ---
        db_name = os.path.basename(db_path)
        self.opened_file_label = ttk.Label(self, text=f"ไฟล์ที่เปิดอยู่: {db_name}", font=("Helvetica", 10, "italic"), anchor="center")
        self.opened_file_label.pack(pady=(5, 0), fill=tk.X)

        # --- (เพิ่ม) ข้อความแจ้งเตือนปี 2569 ---
        self.year_notice_label = ttk.Label(self, text="เงินปันผล และกำไร/ขาดทุน  คิดเฉพาะปี 2569", font=("Helvetica", 10, "bold"), foreground="red", anchor="center")
        self.year_notice_label.pack(pady=(0, 5), fill=tk.X)

        # สร้างหน้าจอสำหรับจัดการธุรกรรม
        self._create_transaction_buttons()
        self.db_manager.withdraw()
        self.deiconify()
        self.attributes('-topmost', True) # ทำให้หน้าต่างนี้อยู่บนสุด
        self.attributes('-topmost', False) # ยกเลิกการอยู่บนสุดเพื่อให้หน้าต่างอื่นทำงานได้

    def reset_to_initial_state(self):
        """ล้างหน้าจอและวิดเจ็ตทั้งหมด กลับไปที่หน้าจอเริ่มต้น"""
        # ล้างวิดเจ็ตทั้งหมด ยกเว้น menubar และ statusbar
        for widget in self.winfo_children():
            if widget is self.status_bar.master:
                continue
            if not isinstance(widget, tk.Menu):
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

    def _try_open_recent_on_startup(self):
        """
        พยายามเปิดไฟล์ฐานข้อมูลล่าสุดเมื่อโปรแกรมเริ่มทำงาน
        คืนค่า True หากสำเร็จ, False หากล้มเหลว (เพื่อให้แสดงหน้าจอเริ่มต้น)
        """
        try:
            if not os.path.exists(self.recent_db_file):
                return False

            with open(self.recent_db_file, 'r') as f:
                db_path = f.read().strip()

            if not db_path or not os.path.exists(db_path):
                return False

            # ตรวจสอบความถูกต้องของไฟล์ก่อนเปิด
            is_valid, _ = self.db_manager._is_schema_valid(db_path)
            if is_valid:
                self.on_database_opened(db_path)
                return True
            else:
                return False
        except Exception:
            return False # หากมีข้อผิดพลาดใดๆ ให้กลับไปหน้าจอเริ่มต้น

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
