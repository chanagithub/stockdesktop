import tkinter as tk
import sqlite3
import os
import sys
import subprocess
from tkinter import ttk
from tkinter import font as tkfont, messagebox
from datetime import datetime
import chmodule 
from tkcalendar import DateEntry # นำเข้าโดยตรง

class Tran_app(tk.Toplevel):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db_path = db_path
        self.title("Transaction window")

        # --- เพิ่มโค้ดตั้งค่าไอคอน ---
        try:
            self.icon_image = tk.PhotoImage(file=chmodule.ChClass.get_resource_path('Graph.png'))
            self.iconphoto(True, self.icon_image)
        except tk.TclError:
            print("ไม่พบไฟล์ไอคอน 'Graph.png' ใน transaction.py")
        
        #center windows
        # --- ขยายขนาดหน้าต่างเพื่อให้มีพื้นที่สำหรับแท็บและจัดกึ่งกลาง ---
        chmodule.ChClass.setwindowcenter(self, 800, 700) # ใช้ขนาด 800x700 ตามที่เคยกำหนด
        self.status_bar = chmodule.ChClass.status_bar("Ready", self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        # self.geometry("800x700") # ลบออกเนื่องจาก setwindowcenter จัดการแล้ว

        self.is_messagebox_active = False # ตัวแปรสำหรับตรวจสอบว่ามี messagebox แสดงอยู่หรือไม่

        self.create_widgets()
        self.deiconify() # แสดงหน้าต่างนี้หลังจากสร้างปุ่มต่าง ๆ เสร็จแล้ว
    
    def create_widgets(self):
        """สร้าง Notebook (แท็บ) สำหรับหน้าจอซื้อและขาย"""
        # --- 1. สร้าง widget Notebook ---
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # --- 2. สร้าง Frame สำหรับแต่ละแท็บ โดยใช้ tk.Frame เพื่อให้กำหนดสีได้ ---
        # และกำหนดสีพื้นหลังโดยตรงด้วย `bg`
        buy_frame = tk.Frame(notebook, bg='#E0F7FA') # สีฟ้าอ่อน
        sell_frame = tk.Frame(notebook, bg='#FFEBEE') # สีแดงอ่อน

        # --- 3. เพิ่ม Frame ทั้งสองเข้าไปใน Notebook ---
        notebook.add(buy_frame, text="ซื้อ")
        notebook.add(sell_frame, text="ขาย")

        # --- 4. สร้าง widget ภายในแท็บ "ซื้อ" ---
        self.create_buy_tab_widgets(buy_frame)

        # --- 5. สร้าง widget ภายในแท็บ "ขาย" ---
        self.create_sell_tab_widgets(sell_frame)
        
    def get_existing_symbols(self):
        """ดึงรายชื่อหุ้นที่เคยซื้อทั้งหมดจากฐานข้อมูล"""
        if not self.db_path:
            return []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT symbol FROM lots ORDER BY symbol ASC")
                symbols = [row[0] for row in cursor.fetchall()]
                return symbols
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            return []

    def create_buy_tab_widgets(self, parent_frame):
        """สร้างช่องกรอกข้อมูลและปุ่มสำหรับแท็บ 'ซื้อ'"""
        # --- ตั้งค่าให้คอลัมน์ที่ 1 (ช่องกรอก) ขยายตามขนาดหน้าต่าง ---
        parent_frame.columnconfigure(1, weight=1)

        # --- สร้าง Labels และ Entries ---
        labels_info = {
            "symbol": "ชื่อหุ้นที่ซื้อ:",
            "buy_date": "วันที่ซื้อ:",
            "volume": "จำนวนหุ้นที่ซื้อ:",
            "price": "ราคาต่อหุ้น:",
            "commission": "ค่าคอมมิชชั่นรวมภาษี:"
        }
        
        self.buy_entries = {} # Dictionary เพื่อเก็บ Entry widgets ไว้ใช้งานภายหลัง

        for i, (key, text) in enumerate(labels_info.items()):
            label = tk.Label(parent_frame, text=text, bg='#E0F7FA', font=("Helvetica", 12))
            label.grid(row=i, column=0, padx=(10, 5), pady=8, sticky='w')

            if key == "buy_date":
                # ใช้ DateEntry สำหรับช่องวันที่
                entry = DateEntry(parent_frame, date_pattern='yyyy-mm-dd', width=18, font=("Helvetica", 12))
                entry.grid(row=i, column=1, padx=(0, 10), pady=8, sticky='w') # จัดชิดซ้าย
            elif key == "symbol":
                entry = ttk.Combobox(parent_frame, font=("Helvetica", 12))
                entry['values'] = self.get_existing_symbols()
                entry.grid(row=i, column=1, padx=(0, 10), pady=8, sticky='ew')
            else:
                entry = ttk.Entry(parent_frame, font=("Helvetica", 12))
                entry.grid(row=i, column=1, padx=(0, 10), pady=8, sticky='ew')

            self.buy_entries[key] = entry

        # --- สร้าง Frame สำหรับจัดวางปุ่ม ---
        button_frame = tk.Frame(parent_frame, bg='#E0F7FA')
        button_frame.grid(row=len(labels_info), column=0, columnspan=2, pady=30)

        # --- สร้างปุ่มต่างๆ ---
        btn_save = ttk.Button(button_frame, text="ตกลง และบันทึกข้อมูล", command=self.save_buy_data)
        btn_clear = ttk.Button(button_frame, text="ล้างหน้าจอ", command=self.clear_buy_entries)
        btn_cancel = ttk.Button(button_frame, text="ยกเลิก และกลับสู่เมนู", command=self.destroy)

        btn_save.pack(side=tk.LEFT, padx=10)
        btn_clear.pack(side=tk.LEFT, padx=10)
        btn_cancel.pack(side=tk.LEFT, padx=10)

    def create_sell_tab_widgets(self, parent_frame):
        """สร้างช่องกรอกข้อมูลและปุ่มสำหรับแท็บ 'ขาย'"""
        parent_frame.columnconfigure(1, weight=1)
        parent_frame.rowconfigure(2, weight=1)  # ให้ส่วนรายการ lot ขยายได้
        
        # --- ส่วนค้นหา Lot ---
        search_frame = tk.Frame(parent_frame, bg='#FFEBEE')
        search_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=(10,5), sticky='ew')
        search_frame.columnconfigure(1, weight=1)

        tk.Label(search_frame, text="ชื่อหุ้น:", bg='#FFEBEE', font=("Helvetica", 12)).grid(row=0, column=0, padx=(0,5))

        # --- เปลี่ยนจาก Entry เป็น Combobox ---
        self.sell_symbol_entry = ttk.Combobox(search_frame, font=("Helvetica", 12))
        self.sell_symbol_entry.grid(row=0, column=1, sticky='ew')
        # ดึงรายชื่อหุ้นที่ถือครองมาใส่ใน Combobox
        self.sell_symbol_entry['values'] = self.get_holding_symbols()
        # ทำให้ค้นหาอัตโนมัติเมื่อกด Enter, คลิกออกจากช่องกรอก, หรือเลือกจากรายการ
        self.sell_symbol_entry.bind('<Return>', self.find_open_lots)
        self.sell_symbol_entry.bind('<FocusOut>', self.find_open_lots)
        self.sell_symbol_entry.bind('<<ComboboxSelected>>', self.find_open_lots)

        # --- ส่วนแสดงรายการ Lot ที่ค้นพบ (checkbox list with select-all) ---
        tk.Label(parent_frame, text="ล็อตที่ถือครอง (เลือกเพื่อขาย):", bg='#FFEBEE', font=("Helvetica", 12)).grid(row=1, column=0, padx=10, pady=5, sticky='w')
        
        # container ที่มี scroll สำหรับรายการ lot
        list_frame = tk.Frame(parent_frame, bg='#FFEBEE', relief=tk.FLAT)
        list_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=(0,10), sticky='nsew')
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        # Select all checkbox
        self.select_all_var = tk.IntVar(value=0)
        self.select_all_cb = tk.Checkbutton(list_frame, text="เลือกทั้งหมด", variable=self.select_all_var, bg='#FFEBEE', command=self._on_select_all)
        self.select_all_cb.grid(row=0, column=0, sticky='w', padx=5, pady=(5,0))

        # scrollable canvas
        self.sell_canvas = tk.Canvas(list_frame, bg='#FFEBEE', highlightthickness=0) # เปลี่ยนเป็น self.sell_canvas
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.sell_canvas.yview)
        self.lot_list_inner = tk.Frame(self.sell_canvas, bg='#FFEBEE')
        self.lot_list_inner.bind("<Configure>", lambda e: self.sell_canvas.configure(scrollregion=self.sell_canvas.bbox("all")))
        self.sell_canvas.create_window((0,0), window=self.lot_list_inner, anchor='nw')
        self.sell_canvas.configure(yscrollcommand=scrollbar.set)

        self.sell_canvas.grid(row=1, column=0, sticky='nsew')
        scrollbar.grid(row=1, column=1, sticky='ns', padx=(2,0))
        list_frame.columnconfigure(0, weight=1)
       


        # เก็บตัวแปรสำหรับ checkbox และข้อมูล lot
        self.lot_check_vars = {}      # lot_id -> IntVar
        self.open_lots_list = []      # list of dicts with lot info (lot_id, lot_number, buy_date, remaining_volume, display_text)

        # --- ส่วนกรอกข้อมูลการขาย ---
        sell_info_frame = tk.Frame(parent_frame, bg='#FFEBEE')
        sell_info_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='ew')
        sell_info_frame.columnconfigure(1, weight=1)

        sell_labels_info = {
            "sell_date": "วันที่ขาย:",
            "sell_price": "ราคาขายต่อหุ้น:",
            "sell_commission": "ค่าภาษี/ค่าธรรมเนียมรวม(บาท):",
            "sell_volume": "จำนวนที่ขาย (เฉพาะกรณีเลือก 1 ล็อต):"
        }

        self.sell_entries = {}
        for i, (key, text) in enumerate(sell_labels_info.items()):
            tk.Label(sell_info_frame, text=text, bg='#FFEBEE', font=("Helvetica", 12)).grid(row=i, column=0, padx=(0,5), pady=5, sticky='w')
            
            if key == "sell_date":
                entry = DateEntry(sell_info_frame, date_pattern='yyyy-mm-dd', width=18, font=("Helvetica", 12))
                entry.grid(row=i, column=1, pady=5, sticky='w')
            else:
                entry = ttk.Entry(sell_info_frame, font=("Helvetica", 12))
                entry.grid(row=i, column=1, pady=5, sticky='ew')

            self.sell_entries[key] = entry

        # ปุ่ม "ขายทั้งหมด" (สำหรับกรณีเลือกเพียง 1 ล็อต จะยังสามารถกดได้)
        self.btn_sell_all = ttk.Button(sell_info_frame, text="ขายทั้งหมด (สำหรับ 1 ล็อต)", command=self.fill_remaining_volume)
        self.btn_sell_all.grid(row=3, column=2, padx=(5,0))

        # --- สรุปสั้นบนหน้าจอ ---
        self.summary_var = tk.StringVar(value="")
        self.summary_label = tk.Label(parent_frame, textvariable=self.summary_var, bg='#FFEBEE', justify='left', font=("Helvetica", 11))
        self.summary_label.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky='w')

        # bind การเปลี่ยนแปลงเพื่ออัพเดตสรุป
        self.sell_entries['sell_price'].bind('<KeyRelease>', lambda e: self.update_summary())
        self.sell_entries['sell_commission'].bind('<KeyRelease>', lambda e: self.update_summary())

        # --- ส่วนปุ่มควบคุม ---
        sell_button_frame = tk.Frame(parent_frame, bg='#FFEBEE')
        sell_button_frame.grid(row=5, column=0, columnspan=3, pady=20)

        btn_save_sell = ttk.Button(sell_button_frame, text="ตกลง และบันทึกการขาย", command=self.save_sell_data)
        btn_clear_sell = ttk.Button(sell_button_frame, text="ล้างหน้าจอ", command=self.clear_sell_entries)
        btn_cancel_sell = ttk.Button(sell_button_frame, text="ยกเลิก และกลับสู่เมนู", command=self.destroy)

        btn_save_sell.pack(side=tk.LEFT, padx=10)
        btn_clear_sell.pack(side=tk.LEFT, padx=10)
        btn_cancel_sell.pack(side=tk.LEFT, padx=10)

    def get_holding_symbols(self):
        """ดึงรายชื่อหุ้นทั้งหมดที่ยังถือครองอยู่ (มีสถานะ OPEN)"""
        if not self.db_path:
            return []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT symbol FROM lots WHERE status = 'OPEN' AND remaining_volume > 0 ORDER BY symbol ASC")
                symbols = [row[0] for row in cursor.fetchall()]
                return symbols
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถดึงรายชื่อหุ้นที่ถือครองได้: {e}", parent=self)
            return []

    def find_open_lots(self, event=None):
        """ค้นหา Lot ที่ยังเปิดขายได้จากฐานข้อมูลและสร้าง checkbox list"""
        # ถ้ามี messagebox แสดงอยู่แล้ว ให้ข้ามการทำงานนี้ไปเลยเพื่อป้องกันการแจ้งเตือนซ้ำซ้อน
        if self.is_messagebox_active:
            return

        symbol = self.sell_symbol_entry.get().strip().upper()
        if not symbol:
            # ถ้าช่องค้นหาว่างเปล่า ก็ไม่ต้องทำอะไรต่อ แค่ล้างข้อมูลเก่าก็พอ
            for widget in self.lot_list_inner.winfo_children():
                widget.destroy()
            self.lot_check_vars.clear()
            return

        # ล้างข้อมูลเก่า
        for widget in self.lot_list_inner.winfo_children():
            widget.destroy()
        self.lot_check_vars.clear()
        self.open_lots_list.clear()
        self.select_all_var.set(0)
        self.update_summary()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                sql = """
                    SELECT lot_id, lot_number, buy_date, remaining_volume, buy_price_per_unit
                    FROM lots
                    WHERE symbol = ? AND status = 'OPEN' AND remaining_volume > 0
                    ORDER BY buy_date ASC
                """
                cursor.execute(sql, (symbol,))
                open_lots = cursor.fetchall()

                if not open_lots:
                    self.is_messagebox_active = True
                    messagebox.showinfo("ไม่พบข้อมูล", f"ไม่พบ Lot ของหุ้น '{symbol}' ที่ยังเปิดขายได้", parent=self)
                    self.is_messagebox_active = False
                    self.sell_symbol_entry.delete(0, tk.END)
                    self.sell_symbol_entry.focus_set()
                    return

                for i, lot in enumerate(open_lots):
                    lot_id, lot_number, buy_date, remaining_volume, buy_price = lot
                    display_text = f"Lot: {lot_number} | ซื้อ: {buy_date} | ราคา: {buy_price:,.2f} | เหลือ: {remaining_volume:,} หุ้น"
                    lot_info = {
                        'lot_id': lot_id,
                        'lot_number': lot_number,
                        'buy_date': buy_date,
                        'remaining_volume': remaining_volume,
                        'display_text': display_text
                    }
                    self.open_lots_list.append(lot_info)

                    var = tk.IntVar(value=0)
                    cb = tk.Checkbutton(self.lot_list_inner, text=display_text, variable=var, bg='#FFEBEE', anchor='w', justify='left',
                                        wraplength=500, command=self._on_lot_selection_changed)
                    cb.grid(row=i, column=0, sticky='w', padx=5, pady=2)
                    self.lot_check_vars[lot_id] = var

                # เลื่อน Canvas กลับไปที่ด้านบนสุด
                self.sell_canvas.yview_moveto(0)

                self.update_summary()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถค้นหาข้อมูล Lot ได้: {e}", parent=self)

    def _on_select_all(self):
        """Toggle all checkboxes"""
        val = bool(self.select_all_var.get())
        for lot_id, var in self.lot_check_vars.items():
            var.set(1 if val else 0)
        self._on_lot_selection_changed()

    def _on_lot_selection_changed(self):
        """เรียกเมื่อมีการเปลี่ยนการเลือกล็อต ปรับสถานะของช่องกรอกและอัพเดตสรุป"""
        selected = [lid for lid, var in self.lot_check_vars.items() if var.get()]
        # อัปเดต select_all state
        if selected and len(selected) == len(self.lot_check_vars):
            self.select_all_var.set(1)
        else:
            self.select_all_var.set(0)

        # ถ้ามากกว่า 1 ล็อต ให้ปิดช่องกรอกจำนวน (บังคับขายทั้งล็อต)
        if len(selected) > 1:
            self.sell_entries['sell_volume'].delete(0, tk.END)
            self.sell_entries['sell_volume'].config(state='disabled')
            self.btn_sell_all.config(state='disabled')
        else:
            self.sell_entries['sell_volume'].config(state='normal')
            self.btn_sell_all.config(state='normal')

        self.update_summary()

    def update_summary(self):
        """คำนวณสรุป: จำนวนล็อต, รวมหุ้น, รวมรับสุทธิ (โดยยังไม่บันทึก)"""
        try:
            selected_lot_ids = [lid for lid, var in self.lot_check_vars.items() if var.get()]
            num_lots = len(selected_lot_ids)
            total_shares = 0
            price = float(self.sell_entries['sell_price'].get()) if self.sell_entries['sell_price'].get().strip() else 0.0
            tax = float(self.sell_entries['sell_commission'].get()) if self.sell_entries['sell_commission'].get().strip() else 0.0

            # รวมจำนวนหุ้นที่จะขาย (สำหรับหลายล็อต = เหลือทั้งหมดของแต่ละล็อต; สำหรับ 1 ล็อต ให้ใช้ค่าที่กรอกถ้ามี)
            if num_lots == 1:
                lot_id = selected_lot_ids[0]
                lot_info = next((l for l in self.open_lots_list if l['lot_id'] == lot_id), None)
                if lot_info:
                    vol_field = self.sell_entries['sell_volume'].get().strip()
                    if vol_field:
                        try:
                            total_shares = float(vol_field.replace(',', ''))
                        except ValueError:
                            total_shares = lot_info['remaining_volume']
                    else:
                        total_shares = lot_info['remaining_volume']
            else:
                for lot_info in self.open_lots_list:
                    if lot_info['lot_id'] in selected_lot_ids:
                        total_shares += lot_info['remaining_volume']

            gross = total_shares * price
            net = gross - tax
            self.summary_var.set(f"เลือก {num_lots} ล็อต\nร่วมหุ้นที่จะขาย: {total_shares:,} หุ้น\nรวมรับสุทธิโดยประมาณ: {net:,.2f} บาท")
        except Exception:
            self.summary_var.set("")

    def _generate_lot_number(self, cursor, symbol, buy_date):
        """สร้าง lot_number รูปแบบ: SYMBOL-YYYY-NNN"""
        year = buy_date.split('-')[0]
        # ค้นหา lot_number ล่าสุดสำหรับหุ้นและปีนั้นๆ
        cursor.execute(
            "SELECT lot_number FROM lots WHERE symbol = ? AND lot_number LIKE ? ORDER BY lot_number DESC LIMIT 1",
            (symbol, f"{symbol}-{year}-%")
        )
        last_lot = cursor.fetchone()

        if last_lot:
            # ถ้ามีอยู่แล้ว, ดึงเลขลำดับสุดท้ายมา +1
            last_seq = int(last_lot[0].split('-')[-1])
            new_seq = last_seq + 1
        else:
            # ถ้ายังไม่มี, เริ่มนับที่ 1
            new_seq = 1
        
        return f"{symbol}-{year}-{new_seq:03d}" # format ให้เป็นเลข 3 หลัก เช่น 001, 002

    def _generate_split_lot_number(self, cursor, original_lot_number):
        """สร้าง lot_number สำหรับล็อตที่ถูกแบ่ง (split) เช่น 'ABC-2023-001-S1'"""
        cursor.execute(
            "SELECT lot_number FROM lots WHERE lot_number LIKE ? ORDER BY lot_number DESC LIMIT 1",
            (f"{original_lot_number}-S%",)
        )
        last_split = cursor.fetchone()
        next_seq = int(last_split[0].split('-S')[-1]) + 1 if last_split else 1
        return f"{original_lot_number}-S{next_seq}"

    def save_buy_data(self):
        """
        ดึงข้อมูล, ตรวจสอบ, คำนวณ, และแสดงกล่องข้อความยืนยันก่อนบันทึก
        """
        # --- 1. ดึงข้อมูลจากช่องกรอก และตัดช่องว่างที่ไม่จำเป็นออก ---
        symbol = self.buy_entries['symbol'].get().strip().upper()
        buy_date = self.buy_entries['buy_date'].get_date().strftime('%Y-%m-%d')
        volume_str = self.buy_entries['volume'].get().strip()
        price_str = self.buy_entries['price'].get().strip()
        commission_str = self.buy_entries['commission'].get().strip()

        # --- 2. ตรวจสอบข้อมูลและแปลงชนิดข้อมูล ---
        try:
            # ตรวจสอบว่ากรอกข้อมูลครบทุกช่องที่จำเป็น
            if not all([symbol, buy_date, volume_str, price_str, commission_str]):
                messagebox.showerror("ข้อมูลไม่ครบถ้วน", "กรุณากรอกข้อมูลให้ครบทุกช่อง")
                return

            volume = float(volume_str.replace(',', ''))
            price = float(price_str)
            commission = float(commission_str)
        except ValueError:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "กรุณาตรวจสอบ 'จำนวนหุ้น', 'ราคา', และ 'ค่าคอมมิชชั่น' ให้เป็นตัวเลขที่ถูกต้อง")
            return

        # --- 3. คำนวณยอดรวม ---
        total_cost = (volume * price) + commission

        # --- 4. สร้างข้อความและแสดงกล่องข้อความยืนยัน ---
        summary_message = (
            f"คุณกำลังจะบันทึกรายการซื้อ:\n\n"
            f"หุ้น: {symbol}\n"
            f"วันที่: {buy_date}\n"
            f"จำนวน: {volume:,} หุ้น\n"
            f"ราคา: {price:,.2f} บาท/หุ้น\n"
            f"ค่าคอม: {commission:,.2f} บาท\n"
            f"รวมเป็นเงินทั้งสิ้น: {total_cost:,.2f} บาท\n\n"
            f"กด 'OK' เพื่อดำเนินการต่อ"
        )
        user_confirmation = messagebox.askokcancel("ยืนยันข้อมูล", summary_message)

        # --- 5. บันทึกข้อมูลลงฐานข้อมูล ---
        if user_confirmation:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    lot_number = self._generate_lot_number(cursor, symbol, buy_date)
                    cursor.execute("""
                        INSERT INTO lots (symbol, lot_number, buy_date, buy_volume, buy_price_per_unit, buy_commission, remaining_volume, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
                    """, (symbol, lot_number, buy_date, volume, price, commission, volume))
                    conn.commit()
                messagebox.showinfo("สำเร็จ", f"บันทึกการซื้อหุ้น {symbol} เรียบร้อยแล้ว", parent=self)
                self.clear_buy_entries()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}", parent=self)

    def clear_buy_entries(self):
        """ล้างข้อความในช่องกรอกข้อมูลทั้งหมด"""
        for key, entry in self.buy_entries.items():
            try:
                if key == 'buy_date':
                    entry.set_date(datetime.now())
                else:
                    entry.config(state='normal')
                    entry.delete(0, tk.END)
            except Exception:
                pass

    def fill_remaining_volume(self):
        """เติมจำนวนหุ้นที่เหลือทั้งหมดในช่อง 'จำนวนที่ขาย' โดยอัตโนมัติ (ใช้ได้เฉพาะเมื่อเลือก 1 ล็อต)"""
        selected = [lid for lid, var in self.lot_check_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("ยังไม่ได้เลือก Lot", "กรุณาเลือก Lot ที่ต้องการขายก่อน", parent=self)
            return

        if len(selected) > 1:
            messagebox.showwarning("ไม่สามารถทำได้", "เมื่อเลือกหลายล็อต จะต้องขายทั้งล็อตเท่านั้น", parent=self)
            return

        lot_id = selected[0]
        lot_info = next((l for l in self.open_lots_list if l['lot_id'] == lot_id), None)
        if not lot_info:
            messagebox.showerror("เกิดข้อผิดพลาด", "ไม่พบข้อมูลล็อตที่เลือก", parent=self)
            return

        self.sell_entries['sell_volume'].delete(0, tk.END)
        self.sell_entries['sell_volume'].insert(0, str(lot_info['remaining_volume']))
        self.update_summary()

    def save_sell_data(self):
        """บันทึกข้อมูลการขายหุ้น (รองรับการขายหลายล็อต โดยแจกจ่ายค่าภาษีตามลำดับ)"""
        # ตรวจสอบการเลือกล็อต
        selected_lot_ids = [lid for lid, var in self.lot_check_vars.items() if var.get()]
        if not selected_lot_ids:
            messagebox.showerror("ข้อมูลไม่ครบถ้วน", "กรุณาเลือกล็อตที่ต้องการขาย", parent=self)
            return

        sell_date = self.sell_entries['sell_date'].get_date().strftime('%Y-%m-%d')
        sell_price_str = self.sell_entries['sell_price'].get().strip()
        sell_commission_str = self.sell_entries['sell_commission'].get().strip()

        if not sell_price_str or not sell_commission_str:
            messagebox.showerror("ข้อมูลไม่ครบถ้วน", "กรุณากรอกวันที่ขาย, ราคาขาย และค่าภาษี/ค่าธรรมเนียม", parent=self)
            return

        try:
            sell_price = float(sell_price_str)
            total_tax = float(sell_commission_str)
        except ValueError:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "กรุณาตรวจสอบ 'ราคา' และ 'ค่าภาษี' ให้เป็นตัวเลข", parent=self)
            return

        # สร้างรายการที่จะขาย: dict lot_id -> sell_volume
        sale_plan = []
        if len(selected_lot_ids) == 1:
            # อนุญาตให้ขายบางส่วน (ต้องกรอกจำนวน)
            vol_str = self.sell_entries['sell_volume'].get().strip()
            if not vol_str:
                messagebox.showerror("ข้อมูลไม่ครบถ้วน", "กรุณากรอกจำนวนหุ้นที่จะขายสำหรับกรณีเลือก 1 ล็อต", parent=self)
                return
            try:
                sell_volume = float(vol_str.replace(',', ''))
            except ValueError:
                messagebox.showerror("ข้อมูลไม่ถูกต้อง", "กรุณากรอกจำนวนหุ้นเป็นตัวเลข", parent=self)
                return
            # เพิ่ม lot_number เข้าไปใน sale_plan
            lot_info = next((l for l in self.open_lots_list if l['lot_id'] == selected_lot_ids[0]), None)
            if not lot_info:
                messagebox.showerror("เกิดข้อผิดพลาด", "ไม่พบข้อมูลล็อตที่เลือก", parent=self)
                return
            if sell_volume <= 0 or sell_volume > lot_info['remaining_volume']:
                messagebox.showerror("จำนวนหุ้นไม่ถูกต้อง", f"จำนวนหุ้นที่ขายต้องมากกว่า 0 และไม่เกิน {lot_info['remaining_volume']:,}", parent=self)
                return
            sale_plan.append({'lot_id': lot_info['lot_id'], 'lot_number': lot_info['lot_number'], 'sell_volume': sell_volume, 'remaining_volume': lot_info['remaining_volume']})
        else:
            # หลายล็อต ต้องขายทั้งล็อต
            for lid in selected_lot_ids:
                lot_info = next((l for l in self.open_lots_list if l['lot_id'] == lid), None)
                if not lot_info:
                    messagebox.showerror("เกิดข้อผิดพลาด", "ไม่พบข้อมูลล็อตที่เลือก", parent=self)
                    return
                sale_plan.append({'lot_id': lot_info['lot_id'], 'lot_number': lot_info['lot_number'], 'sell_volume': lot_info['remaining_volume'], 'remaining_volume': lot_info['remaining_volume']})

        # คำนวณมูลค่าก่อนหักและตรวจสอบว่าพอชำระค่าภาษีรวม
        total_gross = sum(item['sell_volume'] * sell_price for item in sale_plan)
        if total_gross < total_tax:
            messagebox.showerror("ยอดไม่พอ", "มูลค่าการขายรวมไม่เพียงพอสำหรับชำระค่าภาษีที่ระบุ", parent=self)
            return

        # แสดงข้อความยืนยันสรุป
        total_shares = sum(item['sell_volume'] for item in sale_plan)
        total_net = total_gross - total_tax
        summary_message = (
            f"ยืนยันการขาย:\n\n"
            f"จำนวนล็อต: {len(sale_plan)}\n"
            f"ร่วมหุ้นที่จะขาย: {total_shares:,} หุ้น\n"
            f"ราคาขายต่อหุ้น: {sell_price:,.2f} บาท\n"
            f"ค่าภาษี/ค่าธรรมเนียมรวม: {total_tax:,.2f} บาท\n"
            f"รวมรับสุทธิ: {total_net:,.2f} บาท\n\n"
            "กด OK เพื่อบันทึก"
        )
        if not messagebox.askokcancel("ยืนยันการขาย", summary_message, parent=self):
            return

        # แจกจ่ายค่าภาษีตามลำดับล็อต (ล๊อตที่ 1 ถูกหักก่อน ถ้าไม่พอ เอาจากล็อตถัดไป)
        remaining_tax = total_tax
        per_lot_tax = {}  # lot_id -> tax assigned
        for item in sale_plan:
            lot_gross = item['sell_volume'] * sell_price
            assigned = min(lot_gross, remaining_tax)
            per_lot_tax[item['lot_id']] = assigned
            remaining_tax -= assigned
            if remaining_tax <= 0:
                remaining_tax = 0.0

        # --- บันทึกลงฐานข้อมูล (ใช้ Transaction) ---
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row # ทำให้เข้าถึงข้อมูลแบบ dict ได้
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION") # เริ่ม Transaction

            for item in sale_plan:
                original_lot_number = item['lot_number'] # แก้ไข: ใช้ lot_number จาก sale_plan
                sell_vol = item['sell_volume']
                remaining_vol_original = item['remaining_volume']
                assigned_tax = per_lot_tax.get(item['lot_id'], 0.0) # tax ยังคงใช้ lot_id ที่เป็น key

                # ดึงข้อมูลล็อตเดิม
                cursor.execute("SELECT * FROM lots WHERE lot_number = ?", (original_lot_number,)) # แก้ไข: ค้นหาด้วย lot_number
                original_lot = cursor.fetchone()
                if not original_lot: continue
                original_lot_id = original_lot['lot_id'] # ดึง lot_id ที่เป็น primary key มาใช้ต่อ
                is_partial_sale = sell_vol < original_lot['remaining_volume']

                if is_partial_sale:
                    # --- กระบวนการ Lot Splitting ---
                    sold_ratio = sell_vol / original_lot['buy_volume']
                    remaining_ratio = 1.0 - sold_ratio

                    # 1. สร้าง Lot ใหม่สำหรับส่วนที่ขาย
                    new_lot_number = self._generate_split_lot_number(cursor, original_lot['lot_number'])
                    cursor.execute("""
                        INSERT INTO lots (symbol, lot_number, status, buy_date, buy_volume, buy_price_per_unit, buy_commission, remaining_volume)
                        VALUES (?, ?, 'CLOSE', ?, ?, ?, ?, 0)
                    """, (
                        original_lot['symbol'], new_lot_number, original_lot['buy_date'],
                        sell_vol, original_lot['buy_price_per_unit'],
                        original_lot['buy_commission'] * sold_ratio if original_lot['buy_commission'] else 0,
                    ))
                    new_lot_id_db = cursor.lastrowid # lot_id ที่เป็น primary key

                    # 2. บันทึกการขายโดยอ้างอิงถึง Lot ใหม่
                    cursor.execute("""
                        INSERT INTO sales (lot_id, sell_date, sell_volume, sell_price_per_unit, sell_commission)
                        VALUES (?, ?, ?, ?, ?)
                    """, (new_lot_number, sell_date, sell_vol, sell_price, assigned_tax))

                    # 3. แบ่งปันผล/คืนทุน
                    for table in ['dividends', 'capital_returns']:
                        cursor.execute(f"SELECT * FROM {table} WHERE lot_id = ?", (original_lot['lot_number'],))
                        returns = cursor.fetchall()
                        for ret in returns:
                            # 3.1 สร้างรายการใหม่สำหรับ Lot ที่ขาย
                            cursor.execute(
                                f"INSERT INTO {table} (lot_id, payment_date, amount, tax) VALUES (?, ?, ?, ?)" if table == 'dividends'
                                else f"INSERT INTO {table} (lot_id, payment_date, amount) VALUES (?, ?, ?)",
                                (new_lot_number, ret['payment_date'], ret['amount'] * sold_ratio, ret['tax'] * sold_ratio if table == 'dividends' and ret['tax'] else None)
                                if table == 'dividends' else (new_lot_number, ret['payment_date'], ret['amount'] * sold_ratio)
                            )
                            # 3.2 อัปเดตรายการเดิมสำหรับ Lot ที่ยังถือครอง
                            cursor.execute(
                                f"UPDATE {table} SET amount = ?, tax = ? WHERE id = ?" if table == 'dividends'
                                else f"UPDATE {table} SET amount = ? WHERE id = ?",
                                (ret['amount'] * remaining_ratio, ret['tax'] * remaining_ratio if table == 'dividends' and ret['tax'] else None, ret['id'])
                                if table == 'dividends' else (ret['amount'] * remaining_ratio, ret['id'])
                            )

                    # 4. อัปเดต Lot เดิม (ส่วนที่ยังถือครอง)
                    new_remaining_vol = original_lot['remaining_volume'] - sell_vol
                    cursor.execute("UPDATE lots SET remaining_volume = ? WHERE lot_id = ?", (new_remaining_vol, original_lot_id))

                else: # --- กรณีขายทั้งล็อต (Full Sale) ---
                    # 1. บันทึกการขายโดยอ้างอิงถึง lot_number เดิม
                    cursor.execute("""
                        INSERT INTO sales (lot_id, sell_date, sell_volume, sell_price_per_unit, sell_commission)
                        VALUES (?, ?, ?, ?, ?)
                    """, (original_lot['lot_number'], sell_date, sell_vol, sell_price, assigned_tax))

                    # 2. อัปเดตสถานะ Lot เดิมเป็น CLOSE
                    cursor.execute("UPDATE lots SET remaining_volume = 0, status = 'CLOSE' WHERE lot_id = ?", (original_lot_id,))

            conn.commit()  # ยืนยัน Transaction
            messagebox.showinfo("สำเร็จ", "บันทึกการขายเรียบร้อยแล้ว", parent=self)
            self.clear_sell_entries()

        except sqlite3.Error as e:
            if conn:
                conn.rollback() # ยกเลิก Transaction หากเกิดข้อผิดพลาด
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}", parent=self)
        finally:
            if conn:
                conn.close()

    def _save_sell_data_old(self):
        """โค้ดเก่าสำหรับอ้างอิง - ไม่ได้ใช้งานแล้ว"""
        # ... (โค้ดเก่าทั้งหมด) ...
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for item in sale_plan:
                    lid = item['lot_id']
                    vol = item['sell_volume']
                    assigned_tax = per_lot_tax.get(lid, 0.0)
                    cursor.execute("""
                        INSERT INTO sales (lot_id, sell_date, sell_volume, sell_price_per_unit, sell_commission)
                        VALUES (?, ?, ?, ?, ?)
                    """, (lid, sell_date, vol, sell_price, assigned_tax)) # ตรงนี้ต้องใช้ lot_number ไม่ใช่ lot_id
                    # อัปเดต remaining_volume และ status
                    cursor.execute("SELECT remaining_volume FROM lots WHERE lot_id = ?", (lid,))
                    row = cursor.fetchone()
                    if not row:
                        continue
                    new_remaining = row[0] - vol
                    new_status = 'CLOSE' if new_remaining == 0 else 'OPEN'
                    cursor.execute("UPDATE lots SET remaining_volume = ?, status = ? WHERE lot_id = ?", (new_remaining, new_status, lid))

                conn.commit()

            messagebox.showinfo("สำเร็จ", f"บันทึกการขายเรียบร้อยแล้ว", parent=self)
            self.clear_sell_entries()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล (old): {e}", parent=self)

    def clear_sell_entries(self):
        """ล้างข้อมูลในแท็บขายทั้งหมด"""
        self.sell_symbol_entry.delete(0, tk.END)
        # ล้างรายการ checkbox
        for widget in self.lot_list_inner.winfo_children():
            widget.destroy()
        self.lot_check_vars.clear()
        self.open_lots_list.clear()
        self.select_all_var.set(0)
        for key, entry in self.sell_entries.items():
            try:
                if key == 'sell_date':
                    entry.set_date(datetime.now())
                else:
                    entry.config(state='normal')
                    entry.delete(0, tk.END)
            except Exception:
                pass
        self.summary_var.set("")
        # อัปเดตรายการหุ้นใน combobox ด้วย
        self.sell_symbol_entry['values'] = self.get_holding_symbols()

if __name__ == "__main__":
    app = Tran_app()
    app.mainloop()