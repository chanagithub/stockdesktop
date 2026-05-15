from calendar import month
import tkinter as tk
import sqlite3
import os
import sys
import subprocess
from tkinter import ttk
from tkinter import font as tkfont, messagebox
from datetime import date, datetime
import chmodule 
from tkcalendar import DateEntry # นำเข้าโดยตรง

class Tran_app(tk.Toplevel):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db_path = db_path
        self.title("Transaction window")

        # --- เพิ่มโค้ดตั้งค่าไอคอน ---
        try:
            self.icon_image = tk.PhotoImage(file=chmodule.ChClass.get_resource_path('fund.png'))
            self.iconphoto(True, self.icon_image)
        except tk.TclError:
            print("ไม่พบไฟล์ไอคอน 'fund.png' ใน transaction.py")
        
        #center windows
        # --- ขยายขนาดหน้าต่างเพื่อให้มีพื้นที่สำหรับแท็บและจัดกึ่งกลาง ---
        chmodule.ChClass.setwindowcenter(self, 800, 700) # ใช้ขนาด 800x700 ตามที่เคยกำหนด
        self.status_bar = chmodule.ChClass.status_bar("Ready", self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        # self.geometry("800x700") # ลบออกเนื่องจาก setwindowcenter จัดการแล้ว

        self.is_messagebox_active = False # ตัวแปรสำหรับตรวจสอบว่ามี messagebox แสดงอยู่หรือไม่
        self.current_selected_symbol = None # เก็บสัญลักษณ์หุ้นที่เลือกในแท็บขาย
        self.batch_selected_lots = None # เก็บรายการล็อตที่เลือกสำหรับการแก้ไขหลายรายการ
        self.batch_input_type = None # เก็บประเภทข้อมูลที่กรอกในโหมด batch ('volume', 'price', 'amount')
        self.create_widgets()
        self.deiconify() # แสดงหน้าต่างนี้หลังจากสร้างปุ่มต่าง ๆ เสร็จแล้ว
        
        self._check_waiting_lots() # ตรวจสอบข้อมูลที่รอทันทีที่เปิดหน้าต่าง
    
    def create_widgets(self):
        """สร้าง Notebook (แท็บ) สำหรับหน้าจอซื้อและขาย"""
        # --- 1. สร้าง widget Notebook ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # --- NEW: สร้าง Style ที่นี่เพียงครั้งเดียวเพื่อให้ใช้ได้กับทุกแท็บ ---
        style = ttk.Style(self)
        # กำหนดให้ fieldbackground (พื้นหลังของช่องกรอก) เป็นสีเทา (#f0f0f0) เมื่ออยู่ในสถานะ 'disabled'
        style.configure("Disabled.TEntry", fieldbackground="#f0f0f0")
        style.map("Disabled.TEntry", fieldbackground=[("disabled", "#f0f0f0")])

        # --- 2. สร้าง Frame สำหรับแต่ละแท็บ โดยใช้ tk.Frame เพื่อให้กำหนดสีได้ ---
        # และกำหนดสีพื้นหลังโดยตรงด้วย `bg`
        waiting_frame = tk.Frame(self.notebook,bg="#FAF2E0")  # กรอบว่างสำหรับรอการเพิ่มแท็บ
        buy_waiting_frame = tk.Frame(self.notebook, bg='#E0F7FA') # สีฟ้าอ่อนสำหรับสถานะรอซื้อ
        sell_waiting_frame = tk.Frame(self.notebook, bg='#FFEBEE') # สีแดงอ่อนสำหรับสถานะรอขาย
        buy_frame = tk.Frame(self.notebook, bg='#E0F7FA') # สีฟ้าอ่อน
        sell_frame = tk.Frame(self.notebook, bg='#FFEBEE') # สีแดงอ่อน

        # --- 3. เพิ่ม Frame ทั้งสองเข้าไปใน Notebook ---
        self.notebook.add(waiting_frame, text="รอการเพิ่มข้อมูลให้ครบ")
        self.notebook.add(buy_waiting_frame, text="รอการเพิ่มข้อมูลการซื้อให้ครบ")
        self.notebook.add(sell_waiting_frame, text="รอการเพิ่มข้อมูลการขายให้ครบ")
        self.notebook.add(buy_frame, text="ซื้อ")
        self.notebook.add(sell_frame, text="ขาย")

        # --- 4. สร้าง widget ภายในแท็บ "รอการเพิ่มข้อมูลให้ครบ" ---
        self.create_waiting_tab_widgets(waiting_frame)

        # --- 5. สร้าง widget ภายในแท็บ "ซื้อ" ---
        self.create_buy_tab_widgets(buy_frame)

        # --- 6. สร้าง widget ภายในแท็บ "ขาย" ---
        self.create_sell_tab_widgets(sell_frame)

        # --- 7. สร้าง widget ภายในแท็บ "รอซื้อ" ---
        self.create_buy_waiting_tab_widgets(buy_waiting_frame)

        # --- 8. สร้าง widget ภายในแท็บ "รอขาย" ---
        self.create_sell_waiting_tab_widgets(sell_waiting_frame)
        
    def get_existing_symbols(self):
        """ดึงรายชื่อกองทุนที่เคยซื้อทั้งหมดจากฐานข้อมูล"""
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
            "symbol": "ชื่อกองทุนที่ซื้อ:",
            "date": "วันที่ซื้อ:",
            "volume": "จำนวนหน่วยที่ซื้อ:",
            "price": "ราคาต่อหน่วย:",
            "amount": "จำนวนเงินที่จ่าย:"
        }
        
        self.buy_entries = {} # Dictionary เพื่อเก็บ Entry widgets ไว้ใช้งานภายหลัง

        for i, (key, text) in enumerate(labels_info.items()):
            label = tk.Label(parent_frame, text=text, bg='#E0F7FA', font=("Helvetica", 12))
            label.grid(row=i, column=0, padx=(10, 5), pady=8, sticky='w')

            if key == "date":
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

        # --- ทำให้ช่อง 'ราคาต่อหน่วย' ไม่สามารถแก้ไขได้ โดยใช้ Style ที่สร้างไว้แล้ว ---
        self.buy_entries['price'].config(style="Disabled.TEntry", state='disabled')

        # --- เพิ่ม: ผูก Event เพื่อสลับการ disable ระหว่าง volume และ amount ---
        self.buy_entries['volume'].bind("<KeyRelease>", self._handle_buy_input)
        self.buy_entries['amount'].bind("<KeyRelease>", self._handle_buy_input)


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

    def create_waiting_tab_widgets(self, parent_frame):
        """สร้างวิดเจ็ตสำหรับแท็บ 'รอการเพิ่มข้อมูลให้ครบ'"""
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.rowconfigure(2, weight=1) # เปลี่ยนเป็น row 2 เพื่อเพิ่ม label

        # --- Frame สำหรับปุ่ม ---
        top_frame = tk.Frame(parent_frame, bg="#FAF2E0")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        refresh_button = ttk.Button(top_frame, text="รีเฟรชข้อมูล", command=self._load_waiting_lots_data)
        refresh_button.pack(side="left")

        # --- เพิ่ม: ปุ่มสำหรับแก้ไขรายการที่เลือก ---
        edit_button = ttk.Button(top_frame, text="ใส่ข้อมูลต่อให้ครบ", command=self._edit_selected_waiting_lot)
        edit_button.pack(side="left", padx=5)

        # --- เพิ่ม: Label แนะนำการใช้งาน ---
        self.instruction_label = tk.Label(parent_frame, text="ดับเบิ้ลคลิก หรือ เลือกรายการแล้วกดปุ่ม 'ใส่ข้อมูลต่อให้ครบ' เพื่อแก้ไข", bg="#FAF2E0", fg="blue", font=("Helvetica", 10, "italic"))
        self.instruction_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))

        # --- Treeview สำหรับแสดงข้อมูล ---
        self.tree_frame = tk.Frame(parent_frame)
        self.tree_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)

        columns = ('lot_number', 'symbol', 'date', 'volume', 'price', 'amount', 'status')
        self.waiting_tree = ttk.Treeview(self.tree_frame, columns=columns, show='headings')

        # --- กำหนด Header ---
        self.waiting_tree.heading('lot_number', text='Lot Number')
        self.waiting_tree.heading('symbol', text='ชื่อกองทุน')
        self.waiting_tree.heading('date', text='วันที่')
        self.waiting_tree.heading('volume', text='จำนวนหน่วย')
        self.waiting_tree.heading('price', text='ราคา/หน่วย')
        self.waiting_tree.heading('amount', text='จำนวนเงิน')
        self.waiting_tree.heading('status', text='สถานะ')

        # --- กำหนดความกว้างและจัดวางคอลัมน์ ---
        self.waiting_tree.column('lot_number', width=150, anchor=tk.W)
        self.waiting_tree.column('symbol', width=100, anchor=tk.W)
        self.waiting_tree.column('date', width=100, anchor=tk.CENTER)
        self.waiting_tree.column('volume', width=120, anchor=tk.E)
        self.waiting_tree.column('price', width=100, anchor=tk.E)
        self.waiting_tree.column('amount', width=120, anchor=tk.E)
        self.waiting_tree.column('status', width=100, anchor=tk.CENTER)

        # --- สร้าง Scrollbar ---
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.waiting_tree.yview)
        self.waiting_tree.configure(yscrollcommand=vsb.set)

        # --- จัดวาง Treeview และ Scrollbar ---
        self.waiting_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')

        # --- ผูก Event Double Click ---
        self.waiting_tree.bind("<Double-1>", self._show_waiting_lot_editor)

        # --- กำหนด Tags สำหรับสี ---
        self.waiting_tree.tag_configure('buy_waiting', foreground='blue')
        self.waiting_tree.tag_configure('sell_waiting', foreground='red')

        # --- สร้าง Frame สำหรับแก้ไขข้อมูล (ซ่อนไว้ก่อน) ---
        self.waiting_editor_frame = tk.Frame(parent_frame, bg="#FAF2E0")
        self.waiting_editor_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.waiting_editor_frame.grid_remove() # ซ่อน Frame นี้ไว้
        self.waiting_editor_frame.columnconfigure(1, weight=1)

        # --- สร้าง Widgets ใน Frame แก้ไข ---
        self.waiting_editor_entries = {}
        editor_labels = {
            "lot_number": "Lot Number:",
            "symbol": "ชื่อกองทุน:",
            "date": "วันที่:",
            "volume": "จำนวนหน่วย:",
            "price_per_unit": "ราคา/หน่วย:",
            "amount": "จำนวนเงิน:",
            "status": "สถานะ:"
        }

        for i, (key, text) in enumerate(editor_labels.items()):
            label = tk.Label(self.waiting_editor_frame, text=text, bg="#FAF2E0", font=("Helvetica", 12))
            label.grid(row=i, column=0, padx=10, pady=8, sticky="w")
            entry = ttk.Entry(self.waiting_editor_frame, font=("Helvetica", 12))
            entry.grid(row=i, column=1, padx=10, pady=8, sticky="ew")
            self.waiting_editor_entries[key] = entry
            #
        
        self.waiting_editor_entries['price_per_unit'].config(style="Disabled.TEntry", state='disabled') # ปิดแก้ไขช่อง price_per_unit
        # --- ปุ่มสำหรับ Frame แก้ไข ---
        editor_button_frame = tk.Frame(self.waiting_editor_frame, bg="#FAF2E0")
        editor_button_frame.grid(row=len(editor_labels), column=0, columnspan=2, pady=20)

        save_button = ttk.Button(editor_button_frame, text="แสดงข้อมูลสรุป และบันทึกการแก้ไขทั้งหมด", command=self._show_waiting_lot_summary) # เปลี่ยนชื่อปุ่มและ command
        cancel_button = ttk.Button(editor_button_frame, text="ยกเลิกการแก้ไขทั้งหมด", command=self._hide_waiting_lot_editor)

        save_button.pack(side=tk.LEFT, padx=10)
        cancel_button.pack(side=tk.LEFT, padx=10)

    def _edit_selected_waiting_lot(self):
        """
        จัดการการกดปุ่ม 'ใส่ข้อมูลต่อให้ครบ'
        ตรวจสอบว่ามีรายการถูกเลือกหรือไม่ แล้วเรียกฟังก์ชันแก้ไข
        """
        selected_items = self.waiting_tree.selection()
        if not selected_items:
            messagebox.showwarning("ไม่ได้เลือกรายการ", "กรุณาเลือกรายการที่ต้องการแก้ไขก่อน", parent=self)
            return
        
        # ถ้าเลือกรายการเดียว ให้ทำงานเหมือนเดิม
        if len(selected_items) == 1:
            self.waiting_tree.focus(selected_items[0])
            self._show_waiting_lot_editor(None)
            return

        # กรณีเลือกหลายรายการ (Batch Edit)
        selected_records = []
        for item_id in selected_items:
            record_values = self.waiting_tree.item(item_id, "values")
            keys = ('lot_number', 'symbol', 'date', 'volume', 'price', 'amount', 'status')
            record = dict(zip(keys, record_values))
            selected_records.append(record)

        # ตรวจสอบสถานะ (Status Consistency)
        statuses = set(r['status'] for r in selected_records)
        if len(statuses) > 1:
            messagebox.showwarning("ข้อมูลไม่สอดคล้อง", "กรุณาเลือกรายการที่มีสถานะเดียวกัน (ซื้อ/ขาย) เท่านั้น", parent=self)
            return
        status = statuses.pop()

        if status == 'SELL_WAITING':
            symbols = set(r['symbol'] for r in selected_records)
            if len(symbols) > 1:
                messagebox.showwarning("ข้อมูลไม่สอดคล้อง", "สำหรับรายการรอขาย กรุณาเลือกรายการของกองทุนเดียวกัน", parent=self)
                return
            # ไปที่แท็บรอขายของกองทุนนั้น
            self.notebook.select(2)
            self._load_sell_waiting_lots(symbols.pop())
            return

        if status == 'BUY_WAITING':
            # ตรวจสอบว่าข้อมูลที่ขาดหายไปเป็นประเภทเดียวกันหรือไม่
            # ปกติ BUY_WAITING จะมี Amount มา แต่ขาด Volume/Price หรือมี Volume มา แต่ขาด Amount/Price
            need_type = None
            
            for r in selected_records:
                try:
                    vol = float(r['volume'].replace(',', ''))
                except: vol = 0
                try:
                    amt = float(r['amount'].replace(',', ''))
                except: amt = 0
                
                current_need = "unknown"
                if vol == 0 and amt > 0:
                    current_need = "volume_price" # มี Amount ขาด Volume/Price
                elif amt == 0 and vol > 0:
                    current_need = "amount_price" # มี Volume ขาด Amount/Price
                else:
                    # กรณีอื่นๆ ที่อาจเกิดขึ้น (เช่น 0 ทั้งคู่)
                    current_need = "unknown"
                
                if need_type is None:
                    need_type = current_need
                elif need_type != current_need:
                    messagebox.showwarning("ข้อมูลไม่สอดคล้อง", "รายการที่เลือกต้องมีลักษณะข้อมูลที่ต้องการเพิ่มเหมือนกัน (เช่น ต้องการใส่จำนวนหน่วยเหมือนกัน)", parent=self)
                    return
            
            if need_type == "unknown":
                messagebox.showwarning("ข้อมูลไม่ถูกต้อง", "รายการที่เลือกมีข้อมูลไม่สมบูรณ์หรือไม่สามารถระบุสิ่งที่ต้องการเพิ่มได้", parent=self)
                return

            # เข้าสู่โหมดแก้ไขหลายรายการ
            self.notebook.select(1)
            self._setup_batch_buy_editor(selected_records, need_type)

    def _show_waiting_lot_editor(self, event):
        """แสดงฟอร์มแก้ไขข้อมูลเมื่อมีการดับเบิ้ลคลิก"""
        self.batch_selected_lots = None # รีเซ็ตโหมด Batch
        selected_item = self.waiting_tree.focus()
        if not selected_item:
            return
    

        # ดึงข้อมูลจากแถวที่เลือกมาใส่ในฟอร์ม
        record_values = self.waiting_tree.item(selected_item, "values")
        keys = ('lot_number', 'symbol', 'date', 'volume', 'price_per_unit', 'amount', 'status')
        record_dict = dict(zip(keys, record_values))
        status = record_dict.get('status')

        if status == 'BUY_WAITING':
            self.notebook.select(1) # ไปที่แท็บ "รอการเพิ่มข้อมูลการซื้อให้ครบ"
            # นำข้อมูลไปใส่ในฟอร์มของ buy_waiting_frame
            
            # แปลงค่า volume และ amount จาก string เป็น float เพื่อใช้ตรวจสอบ
            try:
                volume_val = float(record_dict.get('volume', '0').replace(',', ''))
            except (ValueError, TypeError):
                volume_val = 0.0
            try:
                amount_val = float(record_dict.get('amount', '0').replace(',', ''))
            except (ValueError, TypeError):
                amount_val = 0.0

            for key, value in record_dict.items():
                if key in self.buy_waiting_entries:
                    self.buy_waiting_entries[key].config(state='normal')
                    self.buy_waiting_entries[key].delete(0, tk.END)
                    self.buy_waiting_entries[key].insert(0, value)

            # ปิดการแก้ไขช่องทั้งหมด ยกเว้นช่องที่ต้องการให้กรอก
            for key, entry in self.buy_waiting_entries.items():
                entry.config(state='disabled')
            if amount_val > 0:
                self.buy_waiting_entries['volume'].config(state='normal')
            elif volume_val > 0:
                self.buy_waiting_entries['amount'].config(state='normal')
        elif status == 'SELL_WAITING':
            self.notebook.select(2) # ไปที่แท็บ "รอการเพิ่มข้อมูลการขายให้ครบ"
            # --- NEW: โหลดข้อมูลล็อตที่รอขายทั้งหมดสำหรับสัญลักษณ์นี้ ---
            symbol_to_load = record_dict.get('symbol')
            if symbol_to_load:
                self._load_sell_waiting_lots(symbol_to_load)




    def _setup_batch_buy_editor(self, records, need_type):
        """ตั้งค่าหน้าจอสำหรับการแก้ไขหลายรายการพร้อมกัน"""
        self.batch_selected_lots = records
        self.batch_input_type = None
        
        # ล้างข้อมูลเดิม
        for entry in self.buy_waiting_entries.values():
            entry.config(state='normal')
            entry.delete(0, tk.END)
        
        # แสดงข้อมูลสรุป
        self.buy_waiting_entries['lot_number'].insert(0, f"Multiple ({len(records)} items)")
        self.buy_waiting_entries['lot_number'].config(state='disabled')
        
        unique_symbols = set(r['symbol'] for r in records)
        symbol_text = list(unique_symbols)[0] if len(unique_symbols) == 1 else "Mixed"
        self.buy_waiting_entries['symbol'].insert(0, symbol_text)
        self.buy_waiting_entries['symbol'].config(state='disabled')
        
        unique_dates = set(r['date'] for r in records)
        date_text = list(unique_dates)[0] if len(unique_dates) == 1 else "Mixed"
        self.buy_waiting_entries['date'].insert(0, date_text)
        self.buy_waiting_entries['date'].config(state='disabled')
        
        self.buy_waiting_entries['status'].insert(0, 'BUY_WAITING')
        self.buy_waiting_entries['status'].config(state='disabled')

        # เปิด/ปิด ช่องกรอกข้อมูลตาม Need Type
        if need_type == "volume_price":
            # มี Amount แล้ว ต้องการ Volume หรือ Price
            self.buy_waiting_entries['amount'].insert(0, "Varies (Fixed per Lot)")
            self.buy_waiting_entries['amount'].config(state='disabled')
            self.buy_waiting_entries['volume'].config(state='normal') # กรอก Volume ได้
            self.buy_waiting_entries['price_per_unit'].config(state='normal') # กรอก Price ได้
        elif need_type == "amount_price":
            # มี Volume แล้ว ต้องการ Amount หรือ Price
            self.buy_waiting_entries['volume'].insert(0, "Varies (Fixed per Lot)")
            self.buy_waiting_entries['volume'].config(state='disabled')
            self.buy_waiting_entries['amount'].config(state='normal') # กรอก Amount ได้
            self.buy_waiting_entries['price_per_unit'].config(state='normal') # กรอก Price ได้

    def _update_price_per_unit(self, volume, amount, event=None):
        """คำนวณและอัปเดตช่อง price_per_unit พร้อม debug log"""
        try:
            # ดึงค่าจากช่อง volume และ amount
            volume_str = self.waiting_editor_entries['volume'].get()
            amount_str = self.waiting_editor_entries['amount'].get()
            # Debug: แสดงค่าที่อ่านได้
            
            # แปลงเป็น float (ลบ comma ถ้ามี)
            volume = float(volume_str.replace(',', '')) if volume_str and volume_str.replace(',', '').replace('.', '', 1).isdigit() else 0
            amount = float(amount_str.replace(',', '')) if amount_str and amount_str.replace(',', '').replace('.', '', 1).isdigit() else 0


         
            # ตรวจสอบว่ามีค่าทั้งคู่และ volume > 0
            if volume or amount  > 0:
                
                price = self._calculate_price_per_unit(volume, amount)
                
                
                # อัปเดตช่อง price_per_unit
                self.waiting_editor_entries['price_per_unit'].delete(0, tk.END)
                self.waiting_editor_entries['price_per_unit'].insert(0, f"{price:.2f}")
            
            else:
                # ถ้าไม่มีค่าหรือ volume=0 ให้ล้างช่อง
            
                self.waiting_editor_entries['price_per_unit'].delete(0, tk.END)

        except Exception as e:
            # Debug error
            print(f"[DEBUG] Error in _update_price_per_unit: {e}")
            self.waiting_editor_entries['price_per_unit'].delete(0, tk.END)

    def _hide_waiting_lot_editor(self):
        """ซ่อนฟอร์มแก้ไขและกลับไปแสดงตาราง"""
        self.waiting_editor_frame.grid_remove()
        self.instruction_label.grid() # แสดง Label แนะนำอีกครั้ง
        self.tree_frame.grid()

    def create_buy_waiting_tab_widgets(self, parent_frame):
        """สร้างวิดเจ็ตสำหรับแท็บ 'รอการเพิ่มข้อมูลการซื้อให้ครบ'"""
        parent_frame.columnconfigure(1, weight=1)

        labels_info = {
            "lot_number": "Lot Number:",
            "symbol": "ชื่อกองทุน:",
            "date": "วันที่:",
            "volume": "จำนวนหน่วย:",
            "price_per_unit": "ราคา/หน่วย:",
            "amount": "จำนวนเงิน:",
            "status": "สถานะ:"
        }

        self.buy_waiting_entries = {}
        for i, (key, text) in enumerate(labels_info.items()):
            label = tk.Label(parent_frame, text=text, bg='#E0F7FA', font=("Helvetica", 12))
            label.grid(row=i, column=0, padx=10, pady=8, sticky="w")
            entry = ttk.Entry(parent_frame, font=("Helvetica", 12))
            entry.grid(row=i, column=1, padx=10, pady=8, sticky="ew")
            self.buy_waiting_entries[key] = entry

        # ทำให้บางช่องไม่สามารถแก้ไขได้
        self.buy_waiting_entries['lot_number'].config(state='disabled')
        self.buy_waiting_entries['symbol'].config(state='disabled')
        self.buy_waiting_entries['date'].config(state='disabled')
        self.buy_waiting_entries['status'].config(state='disabled')
        self.buy_waiting_entries['price_per_unit'].config(state='disabled')

        # ผูก Event เพื่อคำนวณราคาอัตโนมัติ
        self.buy_waiting_entries['volume'].bind("<KeyRelease>", lambda event: self._on_buy_waiting_input('volume'))
        self.buy_waiting_entries['amount'].bind("<KeyRelease>", lambda event: self._on_buy_waiting_input('amount'))
        self.buy_waiting_entries['price_per_unit'].bind("<KeyRelease>", lambda event: self._on_buy_waiting_input('price'))

        # --- ปุ่มสำหรับ Frame แก้ไข ---
        editor_button_frame = tk.Frame(parent_frame, bg='#E0F7FA')
        editor_button_frame.grid(row=len(labels_info), column=0, columnspan=2, pady=20)

        save_button = ttk.Button(editor_button_frame, text="แสดงข้อมูลสรุป และบันทึก", command=self._save_buy_waiting_action)
        cancel_button = ttk.Button(editor_button_frame, text="ยกเลิก", command=self._cancel_buy_waiting_edit)

        save_button.pack(side=tk.LEFT, padx=10)
        cancel_button.pack(side=tk.LEFT, padx=10)

    def _cancel_buy_waiting_edit(self):
        self.batch_selected_lots = None
        self.notebook.select(0)

    def _on_buy_waiting_input(self, input_type):
        """จัดการ input และคำนวณค่าที่สัมพันธ์กัน"""
        self.batch_input_type = input_type
        
        # ถ้าไม่ได้อยู่ในโหมด Batch ใช้ logic เดิม
        if not self.batch_selected_lots:
            if input_type != 'price': # ถ้ากรอก volume หรือ amount ให้คำนวณ price
                self._calculate_buy_waiting_price()
            return

        # ถ้าอยู่ในโหมด Batch ไม่ต้องคำนวณอัตโนมัติใน GUI ทันที เพราะค่า Amount/Volume ของแต่ละล็อตไม่เท่ากัน
        # แต่เราจะ track ว่า user กรอกอะไร
        pass

    def _calculate_buy_waiting_price(self, event=None):
        """คำนวณราคาต่อหน่วยในฟอร์ม buy_waiting"""
        try:
            volume_str = self.buy_waiting_entries['volume'].get().replace(',', '')
            amount_str = self.buy_waiting_entries['amount'].get().replace(',', '')
            volume = float(volume_str) if volume_str else 0
            amount = float(amount_str) if amount_str else 0

            if volume > 0 and amount > 0:
                price = amount / volume
                self.buy_waiting_entries['price_per_unit'].config(state='normal')
                self.buy_waiting_entries['price_per_unit'].delete(0, tk.END)
                self.buy_waiting_entries['price_per_unit'].insert(0, f"{price:.4f}")
                self.buy_waiting_entries['price_per_unit'].config(state='disabled')
            else:
                self.buy_waiting_entries['price_per_unit'].config(state='normal')
                self.buy_waiting_entries['price_per_unit'].delete(0, tk.END)
                self.buy_waiting_entries['price_per_unit'].config(state='disabled')
        except (ValueError, ZeroDivisionError):
            self.buy_waiting_entries['price_per_unit'].config(state='normal')
            self.buy_waiting_entries['price_per_unit'].delete(0, tk.END)
            self.buy_waiting_entries['price_per_unit'].config(state='disabled')

    def create_sell_waiting_tab_widgets(self, parent_frame):
        """สร้างวิดเจ็ตสำหรับแท็บ 'รอการเพิ่มข้อมูลการขายให้ครบ'"""
        # --- โครงสร้าง Layout ---
        parent_frame.columnconfigure(1, weight=1)
        parent_frame.rowconfigure(2, weight=1) # ให้พื้นที่ list ขยายได้

        # --- Frame สำหรับกรอกราคาและชื่อหุ้น ---
        info_frame = tk.Frame(parent_frame, bg='#FFEBEE')
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        info_frame.columnconfigure(1, weight=1)

        self.sell_waiting_symbol_label = tk.Label(info_frame, text="กองทุน: -", bg='#FFEBEE', font=("Helvetica", 12, "bold"))
        self.sell_waiting_symbol_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        tk.Label(info_frame, text="ราคาขาย/หน่วย:", bg='#FFEBEE', font=("Helvetica", 12)).grid(row=1, column=0, sticky="w", padx=(0, 10))
        self.sell_waiting_price_entry = ttk.Entry(info_frame, font=("Helvetica", 12))
        self.sell_waiting_price_entry.grid(row=1, column=1, sticky="ew")
        self.sell_waiting_price_entry.bind("<KeyRelease>", self._update_sell_waiting_amounts)

        # --- Frame สำหรับรายการล็อต (มี Scrollbar) ---
        list_frame = tk.Frame(parent_frame, bg='#FFEBEE')
        list_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        list_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)

        # --- Checkbox เลือกทั้งหมด ---
        self.sell_waiting_select_all_var = tk.IntVar()
        select_all_cb = tk.Checkbutton(list_frame, text="เลือกทั้งหมด", variable=self.sell_waiting_select_all_var,
                                       bg='#FFEBEE', command=self._toggle_all_sell_waiting_lots)
        select_all_cb.grid(row=0, column=0, sticky="w", padx=5)

        # --- Canvas สำหรับแสดงรายการ ---
        canvas = tk.Canvas(list_frame, bg='#FFEBEE', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.sell_waiting_list_inner = tk.Frame(canvas, bg='#FFEBEE')
        self.sell_waiting_list_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.sell_waiting_list_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=1, column=0, sticky='nsew')
        scrollbar.grid(row=1, column=1, sticky='ns')

        # --- Label สรุปยอดรวม ---
        self.sell_waiting_total_label = tk.Label(parent_frame, text="รวมเงินที่จะได้รับทั้งหมด: 0.00 บาท",
                                                  bg='#FFEBEE', font=("Helvetica", 12, "bold"), fg="green")
        self.sell_waiting_total_label.grid(row=3, column=0, columnspan=2, sticky="e", padx=10, pady=5)

        # --- Label สรุปกำไร/ขาดทุน ---
        self.sell_waiting_pl_total_label = tk.Label(parent_frame, text="รวมกำไร/ขาดทุน: 0.00 บาท",
                                                     bg='#FFEBEE', font=("Helvetica", 12, "bold"))
        self.sell_waiting_pl_total_label.grid(row=4, column=0, columnspan=2, sticky="e", padx=10, pady=(0, 5))

        # --- ปุ่มควบคุม ---
        button_frame = tk.Frame(parent_frame, bg='#FFEBEE') # แก้ไข: เปลี่ยน row เป็น 5
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        save_button = ttk.Button(button_frame, text="บันทึกการขาย", command=self._save_sell_waiting_data)
        cancel_button = ttk.Button(button_frame, text="ยกเลิก", command=lambda: self.notebook.select(0))
        save_button.pack(side=tk.LEFT, padx=10)
        cancel_button.pack(side=tk.LEFT, padx=10)

        # --- ตัวแปรสำหรับเก็บข้อมูล ---
        self.sell_waiting_lots_data = []

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
        self.sell_symbol_entry['values'] = chmodule.ChClass.get_holding_symbols(self.db_path)
        # ทำให้ค้นหาอัตโนมัติเมื่อกด Enter, คลิกออกจากช่องกรอก, หรือเลือกจากรายการ
        self.sell_symbol_entry.bind('<Return>', self.find_open_lots)
        self.sell_symbol_entry.bind('<FocusOut>', self.find_open_lots)
        self.sell_symbol_entry.bind('<<ComboboxSelected>>', self.find_open_lots)
        
        # --- เพิ่ม Label สำหรับแสดงชื่อหุ้นที่เลือก ---
        self.selected_symbol_display_var = tk.StringVar(value="ยังไม่ได้เลือกหุ้น")
        self.selected_symbol_label = tk.Label(search_frame, textvariable=self.selected_symbol_display_var,
                                              bg='#FFEBEE', font=("Helvetica", 12, "bold"), fg="blue")
        self.selected_symbol_label.grid(row=1, column=0, columnspan=2, padx=(0,5), pady=5, sticky='w')

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
            "sell_volume": "จำนวนหน่วยที่ขาย:",
            "sell_amount": "จำนวนเงินที่ต้องการขาย:", # เพิ่มช่องจำนวนเงิน
            "sell_price": "ราคาขายต่อหน่วย:", # จะถูก disable
            "sell_commission": "ค่าธรรมเนียมรวม(บาท):", # จะถูก disable
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
        # ทำให้  ช่อง  ราคาขาย   และ  ค่า คอมมิชชั้ัั่นเป็น  disabled  เมื่อไม่มีการกรอกข้อมูล
        # NEW: ใช้ Style ที่สร้างไว้แล้ว
        self.sell_entries['sell_price'].config(style="Disabled.TEntry", state='disabled')
        self.sell_entries['sell_commission'].config(style="Disabled.TEntry", state='disabled')

        # NEW: Bind events to handle exclusive input between volume and amount
        self.sell_entries['sell_volume'].bind("<KeyRelease>", self._handle_sell_input)
        self.sell_entries['sell_amount'].bind("<KeyRelease>", self._handle_sell_input)


        # ปุ่ม "ขายทั้งหมด" (สำหรับกรณีเลือกเพียง 1 ล็อต จะยังสามารถกดได้)
        self.btn_sell_all = ttk.Button(sell_info_frame, text="ขายทั้งหมด (สำหรับ 1 ล็อต)", command=self.fill_remaining_volume)
        self.btn_sell_all.grid(row=1, column=2, padx=(5,0)) # ย้ายปุ่มมาอยู่แถวเดียวกับจำนวนหน่วย

        # --- สรุปสั้นบนหน้าจอ ---
        self.summary_var = tk.StringVar(value="")
        self.summary_label = tk.Label(parent_frame, textvariable=self.summary_var, bg='#FFEBEE', justify='left', font=("Helvetica", 11))
        self.summary_label.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky='w')

        # bind การเปลี่ยนแปลงเพื่ออัพเดตสรุป
        self.sell_entries['sell_volume'].bind('<KeyRelease>', lambda e: self.update_summary())
        self.sell_entries['sell_amount'].bind('<KeyRelease>', lambda e: self.update_summary())

        # --- ส่วนปุ่มควบคุม ---
        sell_button_frame = tk.Frame(parent_frame, bg='#FFEBEE')
        sell_button_frame.grid(row=5, column=0, columnspan=3, pady=20)

        btn_save_sell = ttk.Button(sell_button_frame, text="ตกลง และบันทึกการขาย", command=self.save_sell_data)
        btn_clear_sell = ttk.Button(sell_button_frame, text="ล้างหน้าจอ", command=self.clear_sell_entries)
        btn_cancel_sell = ttk.Button(sell_button_frame, text="ยกเลิก และกลับสู่เมนู", command=self.destroy)

        btn_save_sell.pack(side=tk.LEFT, padx=10)
        btn_clear_sell.pack(side=tk.LEFT, padx=10)
        btn_cancel_sell.pack(side=tk.LEFT, padx=10)

    def find_open_lots(self, event=None):
        """ค้นหา Lot ที่ยังเปิดขายได้จากฐานข้อมูลและสร้าง checkbox list"""
        # ถ้ามี messagebox แสดงอยู่แล้ว ให้ข้ามการทำงานนี้ไปเลยเพื่อป้องกันการแจ้งเตือนซ้ำซ้อน
        if self.is_messagebox_active:
            return

        symbol = self.sell_symbol_entry.get().strip().upper()
        if not symbol:
            # ถ้าช่องค้นหาว่างเปล่า ก็ไม่ต้องทำอะไรต่อ แค่ล้างข้อมูลเก่าก็พอ
            self.selected_symbol_display_var.set("ยังไม่ได้เลือกหุ้น") # อัปเดต Label
            for widget in self.lot_list_inner.winfo_children():
                widget.destroy()
            self.lot_check_vars.clear()
            return

        if symbol == self.current_selected_symbol and self.open_lots_list:
            return

        self.selected_symbol_display_var.set(f"หุ้นที่เลือก: {symbol}") # อัปเดต Label
        self.current_selected_symbol = symbol  # เก็บสัญลักษณ์หุ้นที่เลือกไว้ในตัวแปรสถานะ
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
                    SELECT lot_id, lot_number, buy_date, buy_price_per_unit, remaining_volume
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
                    self.selected_symbol_display_var.set(f"ไม่พบ Lot สำหรับ: {symbol}") # อัปเดต Label เมื่อไม่พบ Lot
                    self.sell_symbol_entry.delete(0, tk.END)
                    self.sell_symbol_entry.focus_set()
                    return

                for i, lot in enumerate(open_lots):
                    lot_id, lot_number, buy_date, buy_price_per_unit, remaining_volume = lot
                    display_text = f"Lot: {lot_number} | ซื้อ: {buy_date} | ราคาซื้อ: {buy_price_per_unit} | เหลือ: {remaining_volume:,} หุ้น"
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
            sell_amount_str = self.sell_entries['sell_amount'].get().strip()
            sell_amount = float(sell_amount_str.replace(',', '')) if sell_amount_str else 0.0

            # รวมจำนวนหุ้นที่จะขาย (สำหรับหลายล็อต = เหลือทั้งหมดของแต่ละล็อต; สำหรับ 1 ล็อต ให้ใช้ค่าที่กรอกถ้ามี)
            if num_lots == 1:
                lot_id = selected_lot_ids[0]
                lot_info = next((l for l in self.open_lots_list if l['lot_id'] == lot_id), None)
                if lot_info:
                    vol_field = self.sell_entries['sell_volume'].get().strip().replace(',', '')
                    if vol_field:
                        try:
                            total_shares = float(vol_field)
                        except ValueError:
                            total_shares = lot_info['remaining_volume']
                    else:
                        total_shares = lot_info['remaining_volume']
            else:
                for lot_info in self.open_lots_list:
                    if lot_info['lot_id'] in selected_lot_ids:
                        total_shares += lot_info['remaining_volume']

        
            

            summary_text = f"เลือก {num_lots} ล็อต"
            if total_shares > 0:
                summary_text += f"\nขายจำนวน: {total_shares:,.4f} หน่วย"
            elif sell_amount > 0:
                summary_text += f"\nขายเป็นเงิน: {sell_amount:,.2f} บาท"

            self.summary_var.set(summary_text)
        except Exception:
            self.summary_var.set("")

    def _handle_sell_input(self, event):
        """จัดการการกรอกข้อมูลในแท็บขาย ให้กรอกได้แค่ volume หรือ amount"""
        volume_entry = self.sell_entries['sell_volume']
        amount_entry = self.sell_entries['sell_amount']

        # ตรวจสอบว่าช่องไหนที่กำลังถูกพิมพ์
        if event.widget == volume_entry:
            print("DEBUG: Typing in volume entry...") # DEBUG
            if volume_entry.get().strip():
                # ถ้ามีข้อความในช่อง volume, ให้ล้างและปิดช่อง amount
                amount_entry.delete(0, tk.END)
                amount_entry.config(state='disabled', style="Disabled.TEntry")
            else:
                # ถ้าลบข้อความออกหมด, ให้เปิดช่อง amount กลับมา
                amount_entry.config(state='normal')
        elif event.widget == amount_entry:
            print("DEBUG: Typing in amount entry...") # DEBUG
            if amount_entry.get().strip():
                # ถ้ามีข้อความในช่อง amount, ให้ล้างและปิดช่อง volume
                volume_entry.delete(0, tk.END)
                volume_entry.config(state='disabled', style="Disabled.TEntry")
            else:
                # ถ้าลบข้อความออกหมด, ให้เปิดช่อง volume กลับมา
                volume_entry.config(state='normal')

    def _check_waiting_lots(self):
        """
        ตรวจสอบตาราง waiting_lots เมื่อเปิดหน้าต่าง
        และแสดงข้อความแจ้งเตือนหากมีข้อมูลค้างอยู่
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM waiting_lots")
                # ถ้ามีข้อมูล ให้โหลดข้อมูลมาแสดง
                if cursor.fetchone()[0] > 0:
                    self._load_waiting_lots_data()
        except sqlite3.Error as e:
            print(f"ไม่สามารถตรวจสอบตาราง waiting_lots ได้: {e}")

    def _load_waiting_lots_data(self):
        """โหลดข้อมูลจากตาราง waiting_lots และแสดงใน Treeview"""
        # ล้างข้อมูลเก่า
        for item in self.waiting_tree.get_children():
            self.waiting_tree.delete(item)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT lot_number, symbol, date, volume, price_per_unit, amount, status FROM waiting_lots ORDER BY date DESC")
                records = cursor.fetchall()

                for record in records:
                    status = record[6] # ดึงค่า status (คอลัมน์ที่ 7)
                    tags_to_apply = () # เริ่มต้นด้วย tag ว่าง (สีปกติ)
                    if status == 'BUY_WAITING':
                        tags_to_apply = ('buy_waiting',)
                    elif status == 'SELL_WAITING':
                        tags_to_apply = ('sell_waiting',)

                    # จัดรูปแบบตัวเลขก่อนแสดงผล
                    formatted_record = list(record)
                    formatted_record[3] = f"{record[3]:,.4f}" # volume
                    formatted_record[4] = f"{record[4]:,.4f}" # price
                    formatted_record[5] = f"{record[5]:,.2f}" # amount
                    self.waiting_tree.insert('', 'end', values=formatted_record, tags=tags_to_apply)
        except sqlite3.Error as e:
            print(f"ไม่สามารถตรวจสอบตาราง waiting_lots ได้: {e}")

    def _handle_buy_input(self, event):
        """
        จัดการการเปิด/ปิดช่องกรอก 'volume' และ 'amount' โดยอัตโนมัติ
        - ถ้ากรอก volume, จะปิด amount
        - ถ้ากรอก amount, จะปิด volume
        """
        volume_entry = self.buy_entries['volume']
        amount_entry = self.buy_entries['amount']

        # ตรวจสอบว่าช่องไหนที่กำลังถูกพิมพ์
        if event.widget == volume_entry:
            # ถ้ามีข้อความในช่อง volume, ให้ปิดช่อง amount
            volume_value = volume_entry.get().strip()
            if volume_value:
                amount_entry.config(state='disabled', style="Disabled.TEntry")
                
            else: # ถ้าลบข้อความออกหมด, ให้เปิดช่อง amount กลับมา
                amount_entry.config(state='normal')
                
        elif event.widget == amount_entry:
            # ถ้ามีข้อความในช่อง amount, ให้ปิดช่อง volume
            amount_value = amount_entry.get().strip()
            if amount_value:
                volume_entry.config(state='disabled', style="Disabled.TEntry")
                
            else: # ถ้าลบข้อความออกหมด, ให้เปิดช่อง volume กลับมา
                volume_entry.config(state='normal')
                

    def _calculate_price_per_unit(self, volume_str, amount_str):
        """คำนวณราคาต่อหน่วยจากจำนวนเงินและจำนวนหน่วยโดยอัตโนมัติ"""
        print("step 1 Enter calculate_price_per_unit")

        print ("step 2 Input Values", f"Volume Input: {volume_str}, Amount Input: {amount_str}")  


        try:
            # ถ้าไม่ได้ส่งค่ามา ให้ดึงจาก entry โดยตรง
            current_volume_str = volume_str if volume_str is not None else self.buy_entries['volume'].get().strip()
            current_amount_str = amount_str if amount_str is not None else self.buy_entries['amount'].get().strip()

            # แปลงค่าเป็น float ถ้ามีข้อมูล, ถ้าไม่มีให้เป็น None
            volume = float(str(current_volume_str).replace(',', '')) if current_volume_str else None
            amount = float(str(current_amount_str).replace(',', '')) if current_amount_str else None

            price = None
            if volume is not None and amount is not None and volume > 0:    
                price = amount / volume
            messagebox.showinfo("step 3 Values", f"Volume: {volume}, Amount: {amount}")    

            messagebox.showinfo("step 4 Calculated Price", f"Calculated price per unit: {price}")  

            # อัปเดตช่องราคา
            self.buy_entries['price'].config(state='normal')
            self.buy_entries['price'].delete(0, tk.END)
            if price is not None:
                self.buy_entries['price'].insert(0, f"{price:.4f}")
            self.buy_entries['price'].config(state='disabled')
            messagebox.showinfo("Updated Price", f"Updated price entry with: {price:.4f}")
        except (ValueError, ZeroDivisionError) as e:
            # กรณีข้อมูลไม่ถูกต้อง, ล้างช่องราคา
            self.buy_entries['price'].config(state='normal')
            self.buy_entries['price'].delete(0, tk.END)
            self.buy_entries['price'].config(state='disabled')

    def save_buy_data(self):
        """
        ดึงข้อมูล, ตรวจสอบ, คำนวณ, และแสดงกล่องข้อความยืนยันก่อนบันทึก
        """
        # --- 1. ดึงข้อมูลจากช่องกรอก และตัดช่องว่างที่ไม่จำเป็นออก ---
        symbol = self.buy_entries['symbol'].get().strip().upper()
        date = self.buy_entries['date'].get_date().strftime('%Y-%m-%d')
        volume_str = self.buy_entries['volume'].get().strip() or '0'
        price_str = self.buy_entries['price'].get().strip() or '0' # ดึงค่าที่คำนวณได้จากช่อง price
        amount_str = self.buy_entries['amount'].get().strip() or '0'



        volume = float(volume_str)  # แปลงเป็น float เพื่อรองรับทศนิยม
        price = float(price_str)
        amount = float(amount_str)


        # --- 4. สร้างข้อความและแสดงกล่องข้อความยืนยัน ---
        summary_message = (
            f"คุณกำลังจะบันทึกรายการซื้อ:\n\n"
            f"กองทุน: {symbol}\n"
            f"วันที่: {date}\n"
            f"จำนวน: {volume:,} หน่วย\n"
            f"ราคา: {price:,.2f} บาท/หน่วย\n"
            f"จำนวนเงินที่จ่าย: {amount:,.2f} บาท\n\n"
            f"กด 'OK' เพื่อดำเนินการต่อ"
        )
        user_confirmation = messagebox.askokcancel("ยืนยันข้อมูล", summary_message)

        # --- 5. บันทึกข้อมูลลงฐานข้อมูล ---  
        if user_confirmation:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    lot_number = chmodule.ChClass.generate_lot_number(cursor, symbol, date)
                    status = 'BUY_WAITING'
                    
                    cursor.execute("""
                        INSERT INTO waiting_lots (symbol, lot_number, date, volume, price_per_unit, amount, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (symbol, lot_number, date, volume, price, amount, status))
                    conn.commit()
                messagebox.showinfo("สำเร็จ", f"บันทึกการซื้อหุ้น {symbol} เรียบร้อยแล้ว", parent=self)
                self.clear_buy_entries()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}", parent=self)

    def clear_buy_entries(self):
        """ล้างข้อความในช่องกรอกข้อมูลทั้งหมด"""
        for key, entry in self.buy_entries.items():
            try:
                # เปิดการใช้งานทุกช่องก่อนล้าง (ยกเว้น price ที่ disable ถาวร)
                if key != 'price':
                    entry.config(state='normal')
                entry.delete(0, tk.END)
            except Exception:
                pass
        # คืนค่า price ให้เป็น disabled เหมือนเดิมหลังล้าง
        self.buy_entries['price'].config(state='disabled')

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
        """บันทึกข้อมูลการขายหุ้นกองทุนใน waiting_lots โดยรับข้อมูลแต่จำนวนหน่วย หรือจำนวนเงิน"""
        # 1. ตรวจสอบการเลือกล็อต
        selected_lot_ids = [lid for lid, var in self.lot_check_vars.items() if var.get()]
        if not selected_lot_ids:
            messagebox.showerror("ข้อมูลไม่ครบถ้วน", "กรุณาเลือกล็อตที่ต้องการทำรายการขาย", parent=self)
            return

        # 2. ดึงข้อมูลจากฟอร์ม
        sell_date = self.sell_entries['sell_date'].get_date().strftime('%Y-%m-%d')
        sell_volume_str = self.sell_entries['sell_volume'].get().strip().replace(',', '')
        sell_amount_str = self.sell_entries['sell_amount'].get().strip().replace(',', '')


        # ถ้าเลือกหลายล็อต ให้ลบค่าจำนวนหน่วยที่กรอกออก (บังคับขายทั้งล็อต)
        if len(selected_lot_ids) > 1:
            sell_volume_str = ''    
        # 3. ตรวจสอบว่ากรอกข้อมูลมาอย่างน้อย 1 อย่าง (volume หรือ amount)
        elif not sell_volume_str and not sell_amount_str:
            messagebox.showerror("ข้อมูลไม่ครบถ้วน", "กรุณากรอกจำนวนหน่วยที่ขาย หรือ จำนวนเงินที่ต้องการขาย", parent=self)
            return
        try:
            sell_volume = float(sell_volume_str) if sell_volume_str else 0.0
            sell_amount = float(sell_amount_str) if sell_amount_str else 0.0
        except ValueError:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "กรุณาตรวจสอบ 'จำนวนหน่วย' หรือ 'จำนวนเงิน' ให้เป็นตัวเลข", parent=self)
            return
    
        # 4. สร้างข้อความยืนยันสรุป
        summary_message = f"คุณกำลังจะบันทึกการขายหุ้นกองทุน:\n\n"
        summary_message += f"จำนวนล็อตที่เกี่ยวข้อง: {len(selected_lot_ids)}\n"
        if sell_volume > 0:
            summary_message += f"จำนวน {sell_volume:,.4f} หน่วย\n"
        if sell_amount > 0:
            summary_message += f"เป็นเงิน {sell_amount:,.2f} บาท\n"
        summary_message += "\nกด 'OK' เพื่อดำเนินการต่อ"
        
        # 5. แสดงกล่องข้อความยืนยัน และถ้าไม่กด OK ให้ยกเลิก
        if not messagebox.askokcancel("ยืนยันการขาย", summary_message, parent=self):
            return

        # 6. บันทึกลงฐานข้อมูล waiting_lots
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for lot_id in selected_lot_ids:
                    lot_info = next((l for l in self.open_lots_list if l['lot_id'] == lot_id), None)
                    if not lot_info: continue

                    # ถ้ากรอกจำนวนหน่วย ให้ใช้จำนวนหน่วยที่กรอก (เฉพาะกรณีเลือกล็อตเดียว)
                    # ถ้าเลือกหลายล็อต หรือไม่ได้กรอกจำนวนหน่วย ให้ใช้จำนวนหน่วยที่เหลือทั้งหมดของล็อตนั้นๆ
                    current_sell_vol = sell_volume if len(selected_lot_ids) == 1 and sell_volume > 0 else lot_info['remaining_volume']

                    cursor.execute("""
                        INSERT INTO waiting_lots (symbol, lot_number, date, volume, price_per_unit, amount, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (self.current_selected_symbol, lot_info['lot_number'], sell_date, current_sell_vol, 0, sell_amount, 'SELL_WAITING'))

            messagebox.showinfo("สำเร็จ", "บันทึกรายการรอขายเรียบร้อยแล้ว\nกรุณาไปที่แท็บ 'รอการเพิ่มข้อมูลให้ครบ' เพื่อใส่ราคาขาย", parent=self)
            self.clear_sell_entries()
            self._check_waiting_lots() # รีเฟรชข้อมูลในแท็บรอ
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}", parent=self)

    def clear_sell_entries(self):
        """ล้างข้อมูลในแท็บขายทั้งหมด"""
        self.sell_symbol_entry.delete(0, tk.END)
        # ล้างรายการ checkbox
        for widget in self.lot_list_inner.winfo_children():
            widget.destroy()
        self.lot_check_vars.clear()
        self.open_lots_list.clear()
        self.select_all_var.set(0)
        for entry in self.sell_entries.values():
            try:
                entry.config(state='normal')
                entry.delete(0, tk.END)
            except Exception:
                pass
        self.summary_var.set("")
        # อัปเดตรายการหุ้นใน combobox ด้วย
        self.sell_symbol_entry['values'] = chmodule.ChClass.get_holding_symbols(self.db_path)

    def _save_buy_waiting_action(self):
        """ตรวจสอบโหมดและเรียกฟังก์ชันบันทึกที่เหมาะสม"""
        if self.batch_selected_lots:
            self._save_batch_waiting_lots()
        else:
            self._show_waiting_lot_summary()

    def _save_batch_waiting_lots(self):
        """บันทึกข้อมูลหลายรายการพร้อมกัน"""
        input_val_str = ""
        input_val = 0.0
        
        if self.batch_input_type == 'volume':
            input_val_str = self.buy_waiting_entries['volume'].get().replace(',', '')
        elif self.batch_input_type == 'price':
            input_val_str = self.buy_waiting_entries['price_per_unit'].get().replace(',', '')
        elif self.batch_input_type == 'amount':
            input_val_str = self.buy_waiting_entries['amount'].get().replace(',', '')
            
        try:
            input_val = float(input_val_str)
            if input_val <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "กรุณากรอกตัวเลขที่มากกว่า 0", parent=self)
            return

        summary_msg = f"คุณกำลังจะบันทึกข้อมูลสำหรับ {len(self.batch_selected_lots)} รายการ\n"
        summary_msg += f"โดยใช้ {self.batch_input_type.capitalize()}: {input_val:,.4f}\n\n"
        summary_msg += "ระบบจะคำนวณค่าที่ขาดหายไปของแต่ละรายการอัตโนมัติ\nต้องการดำเนินการต่อหรือไม่?"
        
        if not messagebox.askokcancel("ยืนยันการบันทึกแบบกลุ่ม", summary_msg, parent=self):
            return

        try:
            for record in self.batch_selected_lots:
                # ดึงค่าเดิม
                orig_vol = float(record['volume'].replace(',', '')) if record['volume'] else 0
                orig_amt = float(record['amount'].replace(',', '')) if record['amount'] else 0
                
                # คำนวณค่าใหม่
                new_vol = orig_vol
                new_amt = orig_amt
                new_price = 0.0

                if self.batch_input_type == 'volume':
                    new_vol = input_val
                    if new_amt > 0: new_price = new_amt / new_vol
                elif self.batch_input_type == 'amount':
                    new_amt = input_val
                    if new_vol > 0: new_price = new_amt / new_vol
                elif self.batch_input_type == 'price':
                    new_price = input_val
                    if new_amt > 0: new_vol = new_amt / new_price
                    elif new_vol > 0: new_amt = new_vol * new_price
                
                # บันทึกทีละรายการ
                self._save_waiting_lot_data(record['lot_number'], record['symbol'], record['date'], new_vol, new_price, new_amt, show_success=False)
            
            messagebox.showinfo("สำเร็จ", f"บันทึกข้อมูล {len(self.batch_selected_lots)} รายการเรียบร้อยแล้ว", parent=self)
            self.batch_selected_lots = None
            self.notebook.select(0)
            
        except Exception as e:
             messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {e}", parent=self)

    def _show_waiting_lot_summary(self):
        """แสดงข้อมูลสรุปจากฟอร์มแก้ไข (สำหรับรายการเดียว)"""
        try:
            # ใช้ข้อมูลจากฟอร์ม buy_waiting_entries
            lot_number = self.buy_waiting_entries['lot_number'].get().strip()
            symbol = self.buy_waiting_entries['symbol'].get().strip().upper()
            date = self.buy_waiting_entries['date'].get().strip()
            volume_str = self.buy_waiting_entries['volume'].get().strip() or '0'
            # ⚠️ NEW: ลบเครื่องหมายจุลภาคออกก่อน
            volume_str = volume_str.replace('\u200b', '').replace('\xa0', '').replace(',', '')
            price_str = self.buy_waiting_entries['price_per_unit'].get().strip() or '0'
            amount_str = self.buy_waiting_entries['amount'].get().strip() or '0'
            # ⚠️ NEW: ลบเครื่องหมายจุลภาคออกก่อน
            amount_str = amount_str.replace('\u200b', '').replace('\xa0', '').replace(',', '')
            
            volume = float(volume_str)
            amount = float(amount_str)

            if not all([lot_number, symbol, date, volume > 0, amount > 0]):
                messagebox.showerror("ข้อมูลไม่ครบถ้วน", "กรุณากรอกข้อมูลการซื้อให้ครบถ้วนและถูกต้อง", parent=self)
                return

            price = amount / volume

            summary_message = (
                f"ข้อมูลสรุป:\n\n"
                f"ล็อตหมายเลข: {lot_number}\n"
                f"กองทุน: {symbol}\n"
                f"วันที่: {date}\n"
                f"จำนวน: {volume:,.4f} หน่วย\n"
                f"ราคา: {price:,.4f} บาท/หน่วย\n"
                f"จำนวนเงินที่จ่าย: {amount:,.2f} บาท\n\n"
                "กด 'OK' เพื่อบันทึกข้อมูล"
            )
            # 5. แสดงกล่องข้อความยืนยัน
            if messagebox.askokcancel("ยืนยันข้อมูล", summary_message, parent=self):
                self._save_waiting_lot_data(lot_number, symbol, date, volume, price, amount, show_success=True)
        except (ValueError, TypeError):
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "กรุณาตรวจสอบข้อมูลในฟอร์มให้ถูกต้อง", parent=self)    
        except ZeroDivisionError:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "จำนวนหน่วยต้องมากกว่า 0", parent=self)

    def _save_waiting_lot_data(self, lot_number, symbol, date, volume, price, amount, show_success=True):
        """บันทึกข้อมูลจากฟอร์มแก้ไขลงฐานข้อมูล"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. เพิ่มข้อมูลลงในตาราง lots
                cursor.execute("""
                    INSERT INTO lots (lot_number, symbol, buy_date, buy_volume, buy_price_per_unit, status,remaining_volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (lot_number, symbol, date, volume, price, 'OPEN', volume))
                conn.commit()
                #ลยข้อมูลออกจากตาราง waiting_lots
                cursor.execute("DELETE FROM waiting_lots WHERE lot_number = ?", (lot_number,))
                conn.commit()
            
            if show_success:
                messagebox.showinfo("สำเร็จ", f"บันทึกข้อมูลล็อตรอซื้อเรียบร้อยแล้ว", parent=self)
                self.notebook.select(0) # กลับไปที่แท็บแรกเฉพาะเมื่อทำรายการเดียว

            self._load_waiting_lots_data() # โหลดข้อมูลใน treeview ใหม่
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}", parent=self)

    def _hide_waiting_lot_editor(self):
        """ซ่อนฟอร์มแก้ไขและกลับไปแสดงตาราง"""
        self.waiting_editor_frame.grid_remove()
        self.instruction_label.grid() # แสดง Label แนะนำอีกครั้ง
        self.tree_frame.grid()
            
    def _load_sell_waiting_lots(self, symbol):
        """โหลดข้อมูลล็อตที่รอขายสำหรับสัญลักษณ์ที่กำหนดและแสดงใน sell_waiting_frame"""
        # --- 1. ล้างข้อมูลเก่า ---
        for widget in self.sell_waiting_list_inner.winfo_children():
            widget.destroy()
        self.sell_waiting_lots_data.clear()
        self.sell_waiting_price_entry.delete(0, tk.END)
        self.sell_waiting_symbol_label.config(text=f"กองทุน: {symbol}")
        self.sell_waiting_select_all_var.set(0)
        self.sell_waiting_pl_total_label.config(text="รวมกำไร/ขาดทุน: 0.00 บาท", fg="black")
        self._update_sell_waiting_amounts()

        # --- 2. ดึงข้อมูลใหม่จากฐานข้อมูล ---
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        w.lot_number, w.date, w.volume,
                        l.buy_date, l.buy_price_per_unit
                    FROM waiting_lots w
                    JOIN lots l ON w.lot_number = l.lot_number
                    WHERE w.symbol = ? AND w.status = 'SELL_WAITING'
                    ORDER BY w.date ASC, w.lot_number ASC
                """, (symbol,))
                records = cursor.fetchall()

            # --- 3. สร้างวิดเจ็ตสำหรับแต่ละรายการ ---
            for i, (lot_number, sell_date, volume, buy_date, buy_price) in enumerate(records):
                var = tk.IntVar(value=0)
                var.trace_add("write", self._update_sell_waiting_amounts)

                # Frame สำหรับแต่ละแถว
                row_frame = tk.Frame(self.sell_waiting_list_inner, bg='#FFEBEE')
                row_frame.grid(row=i, column=0, sticky="ew", pady=2)

                # NEW: จัดรูปแบบวันที่เป็น DD/MM/YY
                buy_date_obj = datetime.strptime(buy_date, '%Y-%m-%d')
                formatted_buy_date = buy_date_obj.strftime('%d/%m/%y')

                # NEW: สร้างข้อความเริ่มต้นที่สั้นลง
                initial_text = f"{lot_number} ซื้อ {formatted_buy_date}|{buy_price:,.2f}-|{volume:,.4f} u"

                # NEW: รวม Checkbox และ Label ไว้ด้วยกัน
                cb = tk.Checkbutton(row_frame, text=initial_text, variable=var, bg='#FFEBEE', anchor='w')
                cb.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

                self.sell_waiting_lots_data.append({
                    'lot_number': lot_number,
                    'volume': volume,
                    'buy_price': buy_price,
                    'sell_date': sell_date, # เก็บวันที่ขายไว้ด้วย
                    'var': var,
                    'checkbox': cb, # เก็บ widget ของ checkbox
                    'initial_text': initial_text # เก็บข้อความเริ่มต้นไว้
                })

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถโหลดข้อมูลล็อตที่รอขายได้: {e}", parent=self)

    def _toggle_all_sell_waiting_lots(self):
        """เลือก/ไม่เลือก เช็คบ็อกซ์ทั้งหมดในแท็บรอขาย"""
        is_checked = self.sell_waiting_select_all_var.get()
        for lot_data in self.sell_waiting_lots_data:
            lot_data['var'].set(is_checked)
        # การอัปเดตจะถูกเรียกโดย trace บนตัวแปร var อยู่แล้ว

    def _update_sell_waiting_amounts(self, *args):
        """คำนวณและอัปเดตจำนวนเงินที่ได้รับสำหรับแต่ละล็อตและยอดรวม"""
        try:
            price_str = self.sell_waiting_price_entry.get().strip()
            price = float(price_str) if price_str else 0.0
        except ValueError:
            price = 0.0

        total_amount = 0.0
        total_pl = 0.0

        for lot_data in self.sell_waiting_lots_data:
            checkbox = lot_data['checkbox']
            initial_text = lot_data['initial_text']

            if lot_data['var'].get() == 1: # ถ้าถูกเลือก
                volume = lot_data['volume']
                buy_price = lot_data['buy_price']
                
                print ("DEBUG: Calculating for lot:", lot_data['lot_number'],volume, buy_price, price) # DEBUG
                amount = volume * price
                profit_loss = (price - buy_price) * volume

                print ("DEBUG: Calculated amount and P/L:", amount, profit_loss) # DEBUG


                # NEW: สร้างข้อความ P/L และอัปเดต Checkbutton
                pl_color = "green" if profit_loss >= 0 else "red"
                checkbox.config(text=f"{initial_text}   P/L: {profit_loss:,.2f} บาท  ได้รับ: {amount:,.2f} บาท", fg=pl_color)

                total_amount += amount
                total_pl += profit_loss
                print ("DEBUG: Running totals:", total_amount, total_pl) # DEBUG
            else:
                checkbox.config(text=initial_text, fg="black") # คืนค่าข้อความและสีเริ่มต้น

        self.sell_waiting_total_label.config(text=f"รวมเงินที่จะได้รับทั้งหมด: {total_amount:,.2f} บาท")

        # อัปเดต Label สรุปกำไร/ขาดทุนทั้งหมด
        total_pl_color = "green" if total_pl >= 0 else "red"
        self.sell_waiting_pl_total_label.config(text=f"รวมกำไร/ขาดทุน: {total_pl:,.2f} บาท", fg=total_pl_color)


    def _save_sell_waiting_data(self):
        """บันทึกข้อมูลการขายที่กรอกราคาแล้ว"""
        # 1. รวบรวมข้อมูลและตรวจสอบ
        try:
            price_str = self.sell_waiting_price_entry.get().strip()
            if not price_str:
                messagebox.showerror("ข้อมูลไม่ครบถ้วน", "กรุณากรอก 'ราคาขาย/หน่วย'", parent=self)
                return
            sell_price = float(price_str)
        except ValueError:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "'ราคาขาย/หน่วย' ต้องเป็นตัวเลข", parent=self)
            return

        selected_lots = [lot for lot in self.sell_waiting_lots_data if lot['var'].get() == 1]

        if not selected_lots:
            messagebox.showerror("ข้อมูลไม่ครบถ้วน", "กรุณาเลือกล็อตที่ต้องการบันทึกการขายอย่างน้อย 1 รายการ", parent=self)
            return

        # 2. สร้างข้อความสรุปและยืนยัน
        total_lots = len(selected_lots)
        total_volume = sum(lot['volume'] for lot in selected_lots)
        total_amount = total_volume * sell_price

        summary_message = (
            f"ยืนยันการบันทึกข้อมูลการขาย:\n\n"
            f"จำนวนล็อตที่เลือก: {total_lots} ล็อต\n"
            f"จำนวนหน่วยรวม: {total_volume:,.4f} หน่วย\n"
            f"ราคาขายต่อหน่วย: {sell_price:,.4f} บาท\n"
            f"รวมเป็นเงิน: {total_amount:,.2f} บาท\n\n"
            "กด 'OK' เพื่อดำเนินการต่อ"
        )

        if not messagebox.askokcancel("ยืนยันข้อมูล", summary_message, parent=self):
            return

        # 3. บันทึกข้อมูลลงฐานข้อมูล (ใช้ Transaction)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for lot_data in selected_lots:
                    lot_number = lot_data['lot_number']
                   
                    sale_status = chmodule.ChClass.check_sale_type(self.db_path, lot_number, lot_data['volume'] )
                       
                    sell_volume = lot_data['volume']
                    sell_date = lot_data['sell_date']
                    
                    # 3.1 บันทึกลงตาราง sales ในกรณีขายทั้งล็อต
                    if sale_status == 'FULL':

                            cursor.execute("""
                                INSERT INTO sales (lot_id, sell_date, sell_volume, sell_price_per_unit)
                                VALUES (?, ?, ?, ?)
                            """, (lot_number, sell_date, sell_volume, sell_price))
                            

                            
                            
                            # 3.2 อัปเดตตาราง lots
                            cursor.execute("SELECT remaining_volume FROM lots WHERE lot_number = ?", (lot_number,))
                            result = cursor.fetchone()
                            if result:
                                current_remaining = result[0]
                                new_remaining = current_remaining - sell_volume

                                if new_remaining <= 0.00001: # ใช้ค่าน้อยๆ เพื่อป้องกันปัญหา floating point
                                    # ขายหมดล็อต
                                    cursor.execute("""
                                        UPDATE lots SET status = 'CLOSE', remaining_volume = 0
                                        WHERE lot_number = ?
                                    """, (lot_number,))
                                else:
                                    # ขายบางส่วน
                                    cursor.execute("""
                                        UPDATE lots SET remaining_volume = ?
                                        WHERE lot_number = ?
                                    """, (new_remaining, lot_number))

                            cursor.execute("DELETE FROM waiting_lots WHERE lot_number = ?", (lot_number,))
                            
                    else:
                            if sale_status == 'PARTIAL':
                                # NEW: กรณีขายบางส่วน ให้บันทึกในตาราง sales
                                # 1. สร้าง lot_id ใหม่สำหรับตาราง sales โดยเรียกใช้ chmodule (ส่ง db_path แทน cursor)
                                last_seq = chmodule.ChClass.get_last_split_sale_sequence(self.db_path, lot_number)
                                new_sale_lot_id = f"{lot_number}-S{last_seq + 1}"
                                lot_to_add = lot_number
                                print(lot_to_add)
                                # ใช้ lot_id ใหม่สำหรับการบันทึกใน sales
                                # 2. บันทึกข้อมูลการขายลงในตาราง sales
                                cursor.execute("""
                                    INSERT INTO sales (lot_id, sell_date, sell_volume, sell_price_per_unit)
                                    VALUES (?, ?, ?, ?)
                                """, (new_sale_lot_id, sell_date, sell_volume, sell_price))
                                print("Inserted new sale record.")

                                # เพิ่มเรคคอร์ดใหม่ในตาราง lots สำหรับส่วนที่เหลือหลังการขายบางส่วน
                                cursor.execute("""
                                    INSERT INTO lots (lot_number, symbol, buy_date, buy_volume, buy_price_per_unit, status, remaining_volume)
                                    SELECT ?, symbol, buy_date, ?, buy_price_per_unit, 'CLOSE', 0
                                    FROM lots
                                    WHERE lot_number = ? AND NOT EXISTS (SELECT 1 FROM lots WHERE lot_number = ?) 
                                """, (new_sale_lot_id, sell_volume, lot_to_add, new_sale_lot_id))
                                print("Inserted new lot for remaining volume after partial sale.")
                                #conn.commit()
        
                                # 3.2 อัปเดตตาราง lots
                                cursor.execute("SELECT remaining_volume FROM lots WHERE lot_number = ?", (lot_number,))
                                result = cursor.fetchone()
                                if result:
                                    current_remaining = result[0]
                                    new_remaining = current_remaining - sell_volume

                                    if new_remaining <= 0.00001: # ใช้ค่าน้อยๆ เพื่อป้องกันปัญหา floating point
                                        # ขายหมดล็อต
                                        cursor.execute("""
                                            UPDATE lots SET status = 'CLOSE', remaining_volume = 0
                                            WHERE lot_number = ?
                                        """, (lot_number,))
                                    else:
                                        # ขายบางส่วน
                                        cursor.execute("""
                                            UPDATE lots SET remaining_volume = ?
                                            WHERE lot_number = ?
                                        """, (new_remaining, lot_number))

                                self._split_dividends_capital_returns(cursor, lot_number, sell_volume, sell_price, new_sale_lot_id, current_remaining)

                                print("Updated original lot's remaining volume after partial sale.")   


                                # 3.3 ลบออกจาก waiting_lots
                                cursor.execute("DELETE FROM waiting_lots WHERE lot_number = ?", (lot_number,))

                # --- NEW: ย้าย commit มาไว้นอกลูป ---
                # ยืนยันการเปลี่ยนแปลงทั้งหมด (INSERT sales, UPDATE lots, DELETE waiting_lots) ในครั้งเดียว
                conn.commit()



                    # NEW: แบ่งข้อมูล dividends และ capital_returns
                    #self._split_dividends_capital_returns(cursor, lot_number, sell_volume, sell_price)


                   

            # 4. แจ้งผลและรีเฟรชหน้าจอ
            messagebox.showinfo("สำเร็จ", "บันทึกข้อมูลการขายเรียบร้อยแล้ว", parent=self)

            # รีเฟรชข้อมูล
            self._load_waiting_lots_data() # รีเฟรชแท็บหลัก
            self.clear_sell_entries() # รีเฟรช combobox ในแท็บ "ขาย"
            
            # ล้างและกลับไปแท็บหลัก
            self._load_sell_waiting_lots(self.sell_waiting_symbol_label.cget("text").replace("กองทุน: ", "")) # รีเฟรชหน้าปัจจุบัน (อาจจะว่างเปล่า)
            self.notebook.select(0)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}", parent=self)

    def _split_dividends_capital_returns(self, cursor, lot_number, sell_volume, sell_price, target_lot_id, total_volume):
        """แบ่งข้อมูล dividends และ capital_returns เมื่อมีการขายบางส่วน"""
        # 1. คำนวณสัดส่วนจากปริมาณหุ้นก่อนการขาย (total_volume)
        if total_volume <= 0:
            return
            
        sold_ratio = sell_volume / total_volume
        remaining_ratio = 1.0 - sold_ratio  

        # 2. วนลูปตาราง dividends และ capital_returns
        for table in ['dividends', 'capital_returns']:
            # 2.1 ดึงข้อมูลเดิม
            if table == 'dividends':
                cursor.execute(f"SELECT id, payment_date, amount, tax FROM {table} WHERE lot_id = ?", (lot_number,))
            else:
                cursor.execute(f"SELECT id, payment_date, amount FROM {table} WHERE lot_id = ?", (lot_number,))
            
            returns = cursor.fetchall()
            
            for ret in returns:
                if table == 'dividends':
                    ret_id, payment_date, amount, tax = ret[0], ret[1], ret[2], ret[3]
                else:
                    ret_id, payment_date, amount = ret[0], ret[1], ret[2]
                    tax = None
                
                # 2.2 คำนวณส่วนแบ่ง
                sold_amount = amount * sold_ratio
                remaining_amount = amount * remaining_ratio
                sold_tax = tax * sold_ratio if tax is not None else None
                remaining_tax = tax * remaining_ratio if tax is not None else None
                print ("DEBUG: Calculated split amounts:", sold_amount, remaining_amount, sold_tax, remaining_tax) # DEBUG

                # 3. สร้างรายการใหม่สำหรับส่วนที่ขาย
                if table == 'dividends':
                    cursor.execute(
                        f"INSERT INTO {table} (lot_id, payment_date, amount, tax) VALUES (?, ?, ?, ?)",
                        (target_lot_id, payment_date, sold_amount, sold_tax)
                    )
                    print("DEBUG: Inserted new dividend record for sold portion.") # DEBUG
                    #3.1  หากเป็น capital_returns จะไม่มี tax
                else:
                    cursor.execute(
                        f"INSERT INTO {table} (lot_id, payment_date, amount) VALUES (?, ?, ?)",
                        (target_lot_id, payment_date, sold_amount)
                    )

                # 4. อัปเดตรายการเดิมสำหรับส่วนที่เหลือ
                if table == 'dividends':
                    cursor.execute(
                        f"UPDATE {table} SET amount = ?, tax = ? WHERE id = ?",
                        (remaining_amount, remaining_tax, ret_id)
                    )
                    print("DEBUG: Updated original dividend record for remaining portion.") # DEBUG
                else:
                    cursor.execute(
                        f"UPDATE {table} SET amount = ? WHERE id = ?",
                        (remaining_amount, ret_id)
                    )
            print("DEBUG: Updated original capital return record for remaining portion.") # DEBUG






if __name__ == "__main__":
    app = Tran_app()
    app.mainloop()
