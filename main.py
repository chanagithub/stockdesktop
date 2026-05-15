import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

try:
    from PIL import Image, ImageTk
except ImportError:
    # This is a fallback, but it's better to ensure Pillow is installed.
    Image = None
import os
import chmodule

# --- (แก้ไข) Import คลาสของหน้าต่างย่อยๆ แทนการใช้ subprocess ---
from stock import App as StockApp
from funds import App as FundsApp
from managedatabase import Appdb as ManageDbApp # Appdb ถูกเรียกใช้ใน stock.py อยู่แล้ว


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # ตั้งฟอนต์ตาม  OS  ว่าเป้น แมค หรือ วินโดว์
        from tkinter import font as tkfont
        base = tkfont.nametofont("TkDefaultFont")

        self.font_title = base.copy()
        self.font_title.configure(size=12, weight="bold")

        self.font_normal = base.copy()
        self.font_normal.configure(size=10)


        self.title("Stock and funds for me")
        
        # --- ตั้งค่าไอคอนจากไฟล์ PNG ---
        try:
            self.icon_image = tk.PhotoImage(file=chmodule.ChClass.get_resource_path('Graph.png'))
            self.iconphoto(True, self.icon_image)
        except tk.TclError:
            print("ไม่พบไฟล์ไอคอน 'Graph.png'")

        # --- (แก้ไข) สร้าง db_manager ที่นี่เพียงครั้งเดียว ---
        self.db_manager = ManageDbApp(parent=self)
        self.db_manager.withdraw() # ซ่อนไว้ตั้งแต่แรก

        #center windows
        chmodule.ChClass.setwindowcenter(self, 450, 250) # ปรับขนาดหน้าต่างให้กว้างขึ้น
        self.status_bar = chmodule.ChClass.status_bar("Ready", self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- ตั้งค่าให้หน้าต่างอยู่บนสุดเสมอ ---
    
        self.create_widgets()

    def create_widgets(self):
        

    
        
        # Create a label with the custom font
        self.label = ttk.Label(self, text="สวัสดีครับ  นักลงทุน", font=self.font_title)
        self.label.pack(pady=10)

        # --- สร้าง Frame หลักสำหรับแบ่งซ้าย-ขวา ---
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- Frame ด้านซ้ายสำหรับปุ่ม ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(20, 10))

        # --- สร้างและจัดวางปุ่มต่างๆ ---
        buttons_info = [
            # --- (แก้ไข) เปลี่ยน command ให้เรียกฟังก์ชันเปิดหน้าต่างแทน ---
            {"text": "Stock", "command": self.open_stock_window, "tooltip": "จัดการข้อมูลหุ้น"},
            {"text": "Funds", "command": self.open_funds_window, "tooltip": "จัดการข้อมูลกองทุน"},
            {"text": "Manage Database", "command": self.open_managedb_window, "tooltip": "จัดการไฟล์ฐานข้อมูล"}, # ปุ่มนี้ไม่จำเป็นแล้ว เพราะจัดการในหน้า Stock
        ]

        for info in buttons_info:
            button = ttk.Button(button_frame, text=info["text"], command=info["command"])
            button.pack(pady=5, fill=tk.X)
            button.bind("<Enter>", lambda e, text=info["tooltip"]: self._update_statusbar(text))
            button.bind("<Leave>", lambda e: self._update_statusbar("Ready"))

        # --- เพิ่มปุ่มออกจากโปรแกรม แยกต่างหากเพื่อให้มีระยะห่างพิเศษ ---
        exit_button = ttk.Button(button_frame, text="ออกจากโปรแกรม", command=self.destroy)
        # pady=(20, 5) หมายถึง เว้นระยะห่างด้านบน 20 และด้านล่าง 5
        exit_button.pack(pady=(20, 5), fill=tk.X)
        exit_button.bind("<Enter>", lambda e: self._update_statusbar("ปิดโปรแกรม"))
        exit_button.bind("<Leave>", lambda e: self._update_statusbar("Ready"))

        # --- Frame ด้านขวาสำหรับรูปภาพ ---
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        try:
            if Image:
                img = Image.open(chmodule.ChClass.get_resource_path('Graph.png'))
                img_resized = img.resize((150, 150), Image.Resampling.LANCZOS)
                self.display_image = ImageTk.PhotoImage(img_resized)
                
                image_label = ttk.Label(image_frame, image=self.display_image)
                # ใช้ pack ให้รูปอยู่กลาง Frame
                image_label.pack(expand=True)
            else:
                # Fallback text if Pillow is not installed
                fallback_label = ttk.Label(image_frame, text="Graph.png")
                fallback_label.pack(expand=True)

        except (tk.TclError, FileNotFoundError):
            print("ไม่พบไฟล์รูปภาพ 'Graph.png' สำหรับแสดงผล")
            fallback_label = ttk.Label(image_frame, text="ไม่พบรูปภาพ")
            fallback_label.pack(expand=True)

        # --- (แก้ไข) โหลด door_icon ที่นี่ เพื่อส่งต่อไปยังหน้าต่างย่อย ---
        try:
            if Image:
                door_img = Image.open(chmodule.ChClass.get_resource_path('door.png'))
                door_img_resized = door_img.resize((120, 120), Image.Resampling.LANCZOS)
                self.door_icon = ImageTk.PhotoImage(door_img_resized)
        except (tk.TclError, FileNotFoundError):
            self.door_icon = None

        # --- (เพิ่ม) โหลดรูปภาพสำหรับหน้าต่าง Funds ---
        try:
            if Image:
                fund_img = Image.open(chmodule.ChClass.get_resource_path('fund.png'))
                fund_img_resized = fund_img.resize((150, 150), Image.Resampling.LANCZOS)
                self.fund_image = ImageTk.PhotoImage(fund_img_resized)
        except (tk.TclError, FileNotFoundError):
            self.fund_image = None # ถ้าไม่เจอรูป ก็ไม่แสดง

    def _update_statusbar(self, text):
        """Internal method to update the status bar text."""
        chmodule.ChClass.status_bar(text, self)

    # --- (เพิ่ม) ฟังก์ชันสำหรับเปิดหน้าต่างย่อย ---
    def open_stock_window(self):
        """เปิดหน้าต่างจัดการหุ้น"""
        # สร้าง StockApp เป็น Toplevel และส่งอ็อบเจกต์ที่จำเป็นไปให้
        stock_win = StockApp(parent=self, 
                             display_image=self.display_image, 
                             door_icon=self.door_icon,
                             db_manager=self.db_manager) # <-- ส่ง db_manager ไป
        self.withdraw() # ซ่อนหน้าต่างหลัก
        # เมื่อหน้าต่าง stock ปิด, ให้แสดงหน้าต่างหลักอีกครั้ง
        stock_win.protocol("WM_DELETE_WINDOW", lambda: (stock_win.on_close(), self.deiconify()))

    def open_funds_window(self):
        """เปิดหน้าต่างจัดการกองทุน"""
        # สร้าง StockApp เป็น Toplevel และส่งอ็อบเจกต์ที่จำเป็นไปให้
        funds_win = FundsApp(parent=self,
                             display_image=self.fund_image, # <-- แก้ไข: ส่งรูป fund_image ไปแทน
                             door_icon=self.door_icon,
                             db_manager=self.db_manager) # <-- ส่ง db_manager ไป
        self.withdraw() # ซ่อนหน้าต่างหลัก
        # เมื่อหน้าต่าง stock ปิด, ให้แสดงหน้าต่างหลักอีกครั้ง
        funds_win.protocol("WM_DELETE_WINDOW", lambda: (funds_win.on_close(), self.deiconify()))

    def open_managedb_window(self):
        """เปิดหน้าต่างจัดการฐานข้อมูล"""
        # สร้าง instance ใหม่ทุกครั้งที่เรียก เพื่อให้ทำงานเหมือนหน้าต่างย่อย
        db_win = ManageDbApp(parent=self)
        db_win.grab_set()


if __name__ == "__main__":
    app = App()
    app.mainloop()
