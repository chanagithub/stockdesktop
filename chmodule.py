import tkinter as tk
import sys
import os
import sqlite3

class ChClass:
    @staticmethod
    def create_rounded_button(canvas, 
                                x=50, y=50, width=120, height=40, radius=15,
                                text="Button", corner_color="white",
                                bg_color="#3498db", fg_color="white",
                                hover_color="#2980b9", command=None):
            """
            สร้างปุ่มขอบมนบน Canvas พร้อม hover effect
            
            Parameters:
                canvas       : Canvas ที่จะวางปุ่ม
                x, y         : ตำแหน่งมุมบนซ้ายของปุ่ม (default 50,50)
                width,height : ขนาดปุ่ม (default 120x40)
                radius       : รัศมีความโค้ง (default 15)
                text         : ข้อความบนปุ่ม (default "Button")
                corner_color : สีมุมที่ถูกตัดออก (default "white")
                bg_color     : สีพื้นหลังปุ่ม (default น้ำเงิน #3498db)
                fg_color     : สีข้อความ (default ขาว)
                hover_color  : สีเมื่อ hover (default น้ำเงินเข้ม #2980b9)
                command      : ฟังก์ชันเมื่อคลิก (default None)
            """
            # วาดพื้นหลังมุม
            canvas.create_rectangle(x, y, x+width, y+height, fill=corner_color, outline=corner_color)

            # วาดสี่เหลี่ยมขอบมน
            rects = []
            arcs = []
            rects.append(canvas.create_rectangle(x+radius, y, x+width-radius, y+height, fill=bg_color, outline=bg_color))
            rects.append(canvas.create_rectangle(x, y+radius, x+width, y+height-radius, fill=bg_color, outline=bg_color))
            arcs.append(canvas.create_arc(x, y, x+2*radius, y+2*radius, start=90, extent=90, fill=bg_color, outline=bg_color))
            arcs.append(canvas.create_arc(x+width-2*radius, y, x+width, y+2*radius, start=0, extent=90, fill=bg_color, outline=bg_color))
            arcs.append(canvas.create_arc(x, y+height-2*radius, x+2*radius, y+height, start=180, extent=90, fill=bg_color, outline=bg_color))
            arcs.append(canvas.create_arc(x+width-2*radius, y+height-2*radius, x+width, y+height, start=270, extent=90, fill=bg_color, outline=bg_color))

            # ข้อความตรงกลาง
            text_id = canvas.create_text(x+width//2, y+height//2, text=text, fill=fg_color, font=("Arial", 12, "bold"))

            # รวมทั้งหมดเป็น group
            items = rects + arcs + [text_id]

            # hover effect
            def on_enter(event):
                for item in rects+arcs:
                    canvas.itemconfig(item, fill=hover_color, outline=hover_color)
            def on_leave(event):
                for item in rects+arcs:
                    canvas.itemconfig(item, fill=bg_color, outline=bg_color)
            def on_click(event):
                if command:
                    command()

            for item in items:
                canvas.tag_bind(item, "<Enter>", on_enter)
                canvas.tag_bind(item, "<Leave>", on_leave)
                canvas.tag_bind(item, "<Button-1>", on_click)

            return items

    class CreateToolTip:
        """
        สร้าง Tooltip สำหรับ widget
        """
        def __init__(self, widget, text):
            self.widget = widget
            self.text = text
            self.tooltip_window = None
            self.widget.bind("<Enter>", self.show_tooltip)
            self.widget.bind("<Leave>", self.hide_tooltip)

        def show_tooltip(self, event):
            """แสดงหน้าต่าง Tooltip"""
            if self.tooltip_window or not self.text:
                return

            # สร้างหน้าต่าง Toplevel ใหม่
            self.tooltip_window = tw = tk.Toplevel(self.widget)
            # ทำให้ไม่มีขอบหน้าต่าง
            tw.wm_overrideredirect(True)

            # กำหนดตำแหน่งของ Tooltip ให้อยู่ใกล้ๆ เมาส์
            # +20 เพื่อให้ไม่บังตัวชี้เมาส์
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            tw.wm_geometry(f"+{x}+{y}")

            label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                             background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                             font=("tahoma", "8", "normal"))
            label.pack(ipadx=1)

        def hide_tooltip(self, event):
            """ซ่อนและทำลายหน้าต่าง Tooltip"""
            if self.tooltip_window:
                self.tooltip_window.destroy()
            self.tooltip_window = None

    @staticmethod
    def setwindowcenter(window, window_width, window_height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        # ปรับตำแหน่ง Y ให้สูงขึ้น 150 pixels จากจุดกึ่งกลาง
        center_y = int(screen_height/2 - window_height / 2) - 150
        window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        window.resizable(False, False)
    @staticmethod
    def status_bar(texttoshow, parent):
        if not hasattr(parent, '_status_bar_label'):
            status_frame = tk.Frame(parent, background="lightgrey")
            status_frame.pack(side=tk.BOTTOM, fill=tk.X) # เพิ่มการ pack frame ที่นี่
            status_label = tk.Label(status_frame, text=texttoshow, bd=0, anchor=tk.W, padx=10)
            status_label.pack(fill=tk.X, pady=(1, 0))
            parent._status_bar_frame = status_frame
            parent._status_bar_label = status_label
            return status_label
        else:
            parent._status_bar_label.config(text=texttoshow)
            return parent._status_bar_label
    @staticmethod
    def get_resource_path(relative_path):
        """
        หาที่อยู่ของไฟล์ทรัพยากร (เช่น .png, .db) ให้ถูกต้องเสมอ
        ทั้งตอนรันเป็นสคริปต์ปกติและตอนถูกรวมเป็นไฟล์เดียวด้วย PyInstaller
        """
        try:
            # ถ้าโปรแกรมถูก PyInstaller รวมเป็นไฟล์เดียว, sys._MEIPASS จะชี้ไปยังโฟลเดอร์ชั่วคราว
            base_path = sys._MEIPASS
        except Exception:
            # ถ้าไม่ได้รันผ่าน PyInstaller, ให้ใช้ที่อยู่ของ "สคริปต์หลักที่กำลังรันอยู่"
            # (เช่น main.py) เป็น base path เสมอ
            # วิธีนี้จะทำให้การหา path ถูกต้องเสมอ ไม่ว่าจะ import ซ้อนกันกี่ชั้นก็ตาม
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
            # --- เพิ่มโค้ดสำหรับ Debug ---
            #print(f"DEBUG base_path: {base_path}")
            # หากต้องการให้แสดงเป็นกล่องข้อความ ให้ยกเลิกคอมเมนต์บรรทัดด้านล่าง
            #tk.messagebox.showinfo("Debug Path", f"Base Path คือ:\n{base_path}")

        return os.path.join(base_path, relative_path)

    @staticmethod
    def create_canvas_buttons_center_for_main(parent):
        ## Creates all buttons by drawing them on the canvas."""
        button_width = 200
        button_height = 50
        start_x = (400 - button_width) / 2 # Center the buttons
        
        buttons_to_create = [
            (10, "หุ้น", "คลิกเพื่อเข้าสู่โปรแกรมจัดการข้อมูลหุ้น"),
            (50, "กองทุนรวม", "คลิกเพื่อเข้าสู่โปรแกรมจัดการข้อมูลกองทุนรวม"),
            (90, "ทำงานกับฐานข้อมูล ", "คลิกเพื่อเข้าสู่โปรแกรมจัดการฐานข้อมูล")
        ]

        for y_pos, text, tooltip in buttons_to_create:
            parent.create_button(start_x, y_pos, button_width, button_height, text, tooltip)

    @staticmethod
    def create_canvas_buttons_center_for_data_management(parent):
        ## Creates all buttons by drawing them on the canvas."""
        button_width = 200
        button_height = 50
        start_x = (400 - button_width) / 2 # Center the buttons
        
        buttons_to_create = [
            (10, "สร้างฐานข้อมูลใหม่", "คลิกเพื่อสร้างฐานข้อมูลหุ้นใหม่"),
            (50, "เปิดไฟล์ฐานข้อมูล", "คลิกเพื่อเปิดไฟล์ฐานข้อมูลหุ้นที่มีอยู่แล้ว"),
            (90, "ปิดไฟล์ทุกไฟล์ และออกจากหน้าต่างนี้ ", "คลิกเพื่อเออก")
            
        ]

        for y_pos, text, tooltip in buttons_to_create:
            parent.create_button(start_x, y_pos, button_width, button_height, text, tooltip)
    @staticmethod
    def generate_lot_number(cursor, symbol, buy_date):
        """สร้าง lot_number รูปแบบ: SYMBOL-YYYYMMDD-NNN"""
        year = buy_date.split('-')[0]
        month = buy_date.split('-')[1]
        day = buy_date.split('-')[2]
        date_to_rec = f"{year}{month.zfill(2)}{day.zfill(2)}"

        # ค้นหา lot_number ล่าสุดสำหรับหุ้นและวันนั้นๆ
        cursor.execute(
            "SELECT lot_number FROM waiting_lots WHERE symbol = ? AND lot_number LIKE ? ORDER BY lot_number DESC LIMIT 1",
            (symbol, f"{symbol}-{date_to_rec}-%")
        )
        last_lot = cursor.fetchone()

        if last_lot:
            # ถ้ามีอยู่แล้ว, ดึงเลขลำดับสุดท้ายมา +1
            last_seq = int(last_lot[0].split('-')[-1])
            new_seq = last_seq + 1
        else:
            # ถ้ายังไม่มี, เริ่มนับที่ 1
            new_seq = 1

        return f"{symbol}-{date_to_rec}-{new_seq:03d}"

    @staticmethod
    def get_holding_symbols(db_path):
        """ดึงรายชื่อหุ้นทั้งหมดที่ยังถือครองอยู่ (มีสถานะ OPEN)"""
        if not db_path:
            return []
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT symbol FROM lots WHERE status = 'OPEN' AND remaining_volume > 0 ORDER BY symbol ASC")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database Error in get_holding_symbols: {e}")
            return []

    @staticmethod
    def get_last_split_sale_sequence(db_path, original_lot_number):
        """
        ค้นหาลำดับล่าสุดของ lot ที่ถูกแบ่งขาย (split sale) จากตาราง sales
        โดยจะคืนค่าลำดับล่าสุดเป็นตัวเลข (เช่น 1, 2, 3) หรือคืนค่า 0 หากยังไม่เคยมีการแบ่งขาย
        """
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                # ค้นหา lot_id ที่มีรูปแบบ 'original_lot_number-S%' ในตาราง sales
                # ORDER BY lot_id DESC เพื่อให้แน่ใจว่าได้ค่าล่าสุดเสมอ (เช่น S10 มาก่อน S2)
                cursor.execute("""
                    SELECT lot_id FROM sales 
                    WHERE lot_id LIKE ? 
                    ORDER BY lot_id DESC 
                    LIMIT 1
                """, (f"{original_lot_number}-S%",))
                last_split = cursor.fetchone()

                if last_split:
                    # ดึงตัวเลขหลังจาก '-S'
                    # เช่น "LOT-001-S2" -> split('-S') -> ["LOT-001", "2"] -> [-1] -> "2"
                    last_seq_num = int(last_split[0].split('-S')[-1])
                    return last_seq_num
                else:
                    # ไม่เคยมีการ split มาก่อน
                    return 0
        except (ValueError, IndexError, sqlite3.Error):
            # กรณีเกิดข้อผิดพลาด หรือรูปแบบไม่ถูกต้อง ให้คืนค่า 0 เพื่อความปลอดภัย
            return 0

    @staticmethod
    def check_sale_type(db_path, lot_number, sell_volume):
        """
        ตรวจสอบประเภทการขาย (บางส่วน, ทั้งหมด, หรือผิดพลาด)
        - คืนค่า 'PARTIAL' หากเป็นการขายบางส่วน
        - คืนค่า 'FULL' หากเป็นการขายทั้งหมด
        - คืนค่า 'ERROR' หากจำนวนที่ขายมากกว่าจำนวนคงเหลือ
        - คืนค่า 'NOT_FOUND' หากไม่พบ lot_number
        - คืนค่า 'DB_ERROR' หากเกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล
        """
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT remaining_volume FROM lots WHERE lot_number = ?", (lot_number,))
                result = cursor.fetchone()

                if not result:
                    return 'NOT_FOUND'

                remaining_volume = result[0]

                if sell_volume < remaining_volume:
                    return 'PARTIAL'
                elif abs(sell_volume - remaining_volume) < 0.0001: # เปรียบเทียบ float
                    return 'FULL'
                else: # sell_volume > remaining_volume
                    return 'ERROR'
        except sqlite3.Error as e:
            print(f"Database error in check_sale_type: {e}")
            return 'DB_ERROR'




        