import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont, messagebox
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
import os
import chmodule

# --- Import คลาสหน้าต่างย่อย ---
from stock import App as StockApp
from funds import App as FundsApp
from managedatabase import Appdb as ManageDbApp


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # ตั้งฟอนต์ตาม OS
        base = tkfont.nametofont("TkDefaultFont")
        self.font_title = base.copy()
        self.font_title.configure(size=12, weight="bold")
        self.font_normal = base.copy()
        self.font_normal.configure(size=10)

        self.title("Stock and funds for me")

        # ตั้งค่าไอคอน
        try:
            self.icon_image = tk.PhotoImage(file=chmodule.ChClass.get_resource_path('Graph.png'))
            self.iconphoto(True, self.icon_image)
        except tk.TclError:
            print("ไม่พบไฟล์ไอคอน 'Graph.png'")

        # สร้าง db_manager ที่นี่เพียงครั้งเดียว
        self.db_manager = ManageDbApp(parent=self)
        self.db_manager.withdraw()

        # จัดตำแหน่งหน้าต่าง
        chmodule.ChClass.setwindowcenter(self, 450, 250)
        self.status_bar = chmodule.ChClass.status_bar("Ready", self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.create_widgets()

    def create_widgets(self):
        # Label ทักทาย
        self.label = ttk.Label(self, text="สวัสดีครับ นักลงทุน", font=self.font_title)
        self.label.pack(pady=10)

        # Frame หลัก
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Frame ปุ่ม
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(20, 10))

        buttons_info = [
            {"text": "Stock", "command": self.open_stock_window, "tooltip": "จัดการข้อมูลหุ้น"},
            {"text": "Funds", "command": self.open_funds_window, "tooltip": "จัดการข้อมูลกองทุน"},
            {"text": "Manage Database", "command": self.open_managedb_window, "tooltip": "จัดการไฟล์ฐานข้อมูล"},
        ]

        for info in buttons_info:
            button = ttk.Button(button_frame, text=info["text"], command=info["command"])
            button.pack(pady=5, fill=tk.X)
            button.bind("<Enter>", lambda e, text=info["tooltip"]: self._update_statusbar(text))
            button.bind("<Leave>", lambda e: self._update_statusbar("Ready"))

        exit_button = ttk.Button(button_frame, text="ออกจากโปรแกรม", command=self.destroy)
        exit_button.pack(pady=(20, 5), fill=tk.X)
        exit_button.bind("<Enter>", lambda e: self._update_statusbar("ปิดโปรแกรม"))
        exit_button.bind("<Leave>", lambda e: self._update_statusbar("Ready"))

        # Frame รูปภาพ
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        try:
            if Image:
                img = Image.open(chmodule.ChClass.get_resource_path('Graph.png'))
                img_resized = img.resize((150, 150), Image.Resampling.LANCZOS)
                self.display_image = ImageTk.PhotoImage(img_resized)
                image_label = ttk.Label(image_frame, image=self.display_image)
                image_label.pack(expand=True)
            else:
                fallback_label = ttk.Label(image_frame, text="Graph.png")
                fallback_label.pack(expand=True)
        except (tk.TclError, FileNotFoundError):
            print("ไม่พบไฟล์รูปภาพ 'Graph.png'")
            fallback_label = ttk.Label(image_frame, text="ไม่พบรูปภาพ")
            fallback_label.pack(expand=True)

        # door_icon
        try:
            if Image:
                door_img = Image.open(chmodule.ChClass.get_resource_path('door.png'))
                door_img_resized = door_img.resize((120, 120), Image.Resampling.LANCZOS)
                self.door_icon = ImageTk.PhotoImage(door_img_resized)
        except (tk.TclError, FileNotFoundError):
            self.door_icon = None

        # fund_image
        try:
            if Image:
                fund_img = Image.open(chmodule.ChClass.get_resource_path('fund.png'))
                fund_img_resized = fund_img.resize((150, 150), Image.Resampling.LANCZOS)
                self.fund_image = ImageTk.PhotoImage(fund_img_resized)
        except (tk.TclError, FileNotFoundError):
            self.fund_image = None

    def _update_statusbar(self, text):
        chmodule.ChClass.status_bar(text, self)

    def open_stock_window(self):
        stock_win = StockApp(parent=self,
                             display_image=self.display_image,
                             door_icon=self.door_icon)
        self.withdraw()
        stock_win.protocol("WM_DELETE_WINDOW", lambda: (stock_win.on_close(), self.deiconify()))

    def open_funds_window(self):
        funds_win = FundsApp(parent=self,
                             display_image=self.fund_image,
                             door_icon=self.door_icon
                            )
        self.withdraw()
        funds_win.protocol("WM_DELETE_WINDOW", lambda: (funds_win.on_close(), self.deiconify()))

    def open_managedb_window(self):
        db_win = ManageDbApp(parent=self)
        db_win.grab_set()


if __name__ == "__main__":
    app = App()
    app.mainloop()
