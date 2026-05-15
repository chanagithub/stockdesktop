import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont, messagebox
import subprocess
import os
import chmodule
from create_database import CREATE_LOTS_TABLE, CREATE_DIVIDENDS_TABLE, CREATE_CAPITAL_RETURNS_TABLE # Import AppcreateDB เพื่อเรียกใช้ฟังก์ชัน

# --- ตรวจสอบและติดตั้ง Pillow ---
try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showinfo("ติดตั้งไลบรารี", "กำลังติดตั้งไลบรารี Pillow สำหรับจัดการรูปภาพ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageTk

from managedatabase import Appdb # Import Appdb เพื่อเรียกใช้ฟังก์ชัน

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() # ซ่อนหน้าต่างนี้ไว้ก่อน  รอสร้างปุ่มต่าง ๆ เสร็จก่อนแล้วจึงแสดงหน้าต่างนี้ด้วย self.deiconify()
        self.title("Stock window")

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.recent_db_file = os.path.join(self.script_dir, 'recent_db.txt')

        # --- ตั้งค่าไอคอนจากไฟล์ PNG ---
        try:
            original_icon = tk.PhotoImage(file=os.path.join(self.script_dir, 'Graph.png'))
            self.iconphoto(True, original_icon)

            # --- ย่อขนาดรูปภาพสำหรับแสดงผลในหน้าต่าง ---
            img = Image.open(os.path.join(self.script_dir, 'Graph.png'))
            img_resized = img.resize((150, 150), Image.Resampling.LANCZOS)
            self.display_image = ImageTk.PhotoImage(img_resized)

        except (tk.TclError, FileNotFoundError):
            print("ไม่พบไฟล์ไอคอน 'Graph.png'")
            self.display_image = None # กำหนดให้เป็น None หากไม่พบรูป

        # --- โหลดและย่อขนาดรูปภาพประตูสำหรับปุ่มออก ---
        try:
            door_img = Image.open(os.path.join(self.script_dir, 'door.png'))
            # ย่อให้ขนาดเหมาะสม
            door_img_resized = door_img.resize((120, 120), Image.Resampling.LANCZOS)
            self.door_icon = ImageTk.PhotoImage(door_img_resized)
        except (tk.TclError, FileNotFoundError):
            print("ไม่พบไฟล์ไอคอน 'door.png'")
            self.door_icon = None

        #center windows
        self.db_manager = Appdb(on_open_success=self.on_database_opened) # สร้าง instance ของ Appdb และส่ง callback ไป
        self.db_manager.withdraw() # ซ่อนหน้าต่างของ Appdb ไว้
        chmodule.ChClass.setwindowcenter(self, 500, 320)
        self.status_bar = chmodule.ChClass.status_bar("Ready", self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.create_Menubar()

        # ลองเปิดไฟล์ล่าสุดเมื่อเริ่มต้น ถ้าไม่สำเร็จ ให้แสดงหน้าจอเริ่มต้น
        if not self._try_open_recent_on_startup():
            self.create_widgets()

        self.deiconify() # แสดงหน้าต่างนี้หลังจากสร้างปุ่มต่าง ๆ เสร็จแล้ว
        # เมื่อหน้าต่างหลักนี้ปิด ให้ปิดหน้าต่าง db_manager ที่ซ่อนอยู่ด้วย
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # --- เพิ่มคีย์ลัด (Shortcut) ---
        self.bind("<Control-r>", lambda event: self.open_recent_database())

    def on_close(self):
        self.db_manager.destroy()
        self.destroy()

    def create_Menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        # --- Menu "การทำงาน" ---
        work_menu = tk.Menu(menubar, tearoff=0)
        work_menu.add_command(label="เปิด ไฟล์ฐานข้อมูลล่าสุด", command=self.open_recent_database, accelerator="Ctrl+R")
        work_menu.add_command(label="สร้างฐานข้อมูลใหม่", command=self.create_stock_database)
        work_menu.add_command(label="เปิดไฟล์ฐานข้อมูล", command=self.db_manager.open_database) 
        work_menu.add_separator()
        work_menu.add_command(label="ปิดโปรแกรม", command=self.on_close) 
        menubar.add_cascade(label="การทำงาน", menu=work_menu)

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

        # ล้าง widget เก่าทั้งหมดใน self เพื่อเตรียมสร้างหน้าใหม่
        for widget in self.winfo_children():
            if isinstance(widget, (ttk.Frame, ttk.Label, ttk.Button)) and widget is not self.status_bar:
                widget.destroy()

        self._create_transaction_buttons()
        self.db_manager.withdraw()
        self.deiconify()
        self.attributes('-topmost', True) # ทำให้หน้าต่างนี้อยู่บนสุด
        self.attributes('-topmost', False) # ยกเลิกการอยู่บนสุดเพื่อให้หน้าต่างอื่นทำงานได้

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
        button_width = 300
        button_height = 50
        window_width = 500
        window_height = 300

        # คำนวณตำแหน่งเพื่อจัดกึ่งกลาง และห่างจากขอบล่าง 20 pixels
        x_pos = (window_width - button_width) / 2
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
        # --- สร้าง Frame หลักเพื่อจัดวางรูปภาพและปุ่ม ---
        main_content_frame = ttk.Frame(self)
        main_content_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        # --- ส่วนรูปภาพด้านซ้าย ---
        # ใช้ self.display_image ที่ย่อขนาดแล้ว
        image_label = ttk.Label(main_content_frame, image=self.display_image)
        image_label.pack(side=tk.LEFT, padx=20, pady=10)

        # --- ส่วนปุ่มด้านขวา ---
        button_frame = ttk.Frame(main_content_frame)
        button_frame.pack(side=tk.RIGHT, padx=(10, 20), fill=tk.Y)

        # --- สร้างปุ่มต่างๆ ---
        btn_add_trans = ttk.Button(
            button_frame, text="Add Transaction", 
            command=lambda: subprocess.Popen([
                "python3", 
                "transaction.py", 
                self.db_manager.db_path # ส่ง path ของ db ไปด้วย
            ])   
        )
        btn_add_dividend_return = ttk.Button(
            button_frame, text="เพิ่มข้อมูลปันผล / คืนทุน",
            command=lambda: subprocess.Popen([
                "python3",
                "dividend_return.py",
                self.db_manager.db_path # ส่ง path ของ db ไปด้วย
            ])
        )
        btn_analyze_stock = ttk.Button(
            button_frame, text="วิเคราะห์ภาพรวมพอร์ต",
            command=lambda: subprocess.Popen(["python3", "stock_analyze.py", self.db_manager.db_path]) # ส่ง path ของ db ไปด้วย
        )
        btn_analyze_individual_stock = ttk.Button(
            button_frame, text="วิเคราะห์หุ้นรายตัว",
            command=lambda: subprocess.Popen(["python3", "single_stock_anal.py", self.db_manager.db_path]) # ส่ง path ของ db ไปด้วย
        )
        btn_log = ttk.Button(
            button_frame, text="Log",
            command=lambda: subprocess.Popen(["python3", "stock_log.py", self.db_manager.db_path]) # ส่ง path ของ db ไปด้วย
        )
        
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
    
if __name__ == "__main__":
    app = App()
    app.mainloop()

# stock.py