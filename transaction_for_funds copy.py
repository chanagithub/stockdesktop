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
        
        self._check_waiting_lots() # ตรวจสอบข้อมูลที่รอทันทีที่เปิดหน้าต่าง
    
    def create_widgets(self):
        """สร้าง Notebook (แท็บ) สำหรับหน้าจอซื้อและขาย"""
        # --- 1. สร้าง widget Notebook ---
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # --- 2. สร้าง Frame สำหรับแต่ละแท็บ โดยใช้ tk.Frame เพื่อให้กำหนดสีได้ ---
        # และกำหนดสีพื้นหลังโดยตรงด้วย `bg`
        waiting_frame = tk.Frame(notebook,bg="#FAF2E0")  # กรอบว่างสำหรับรอการเพิ่มแท็บ
        buy_frame = tk.Frame(notebook, bg='#E0F7FA') # สีฟ้าอ่อน
        sell_frame = tk.Frame(notebook, bg='#FFEBEE') # สีแดงอ่อน

        # --- 3. เพิ่ม Frame ทั้งสองเข้าไปใน Notebook ---
        notebook.add(waiting_frame, text="รอการเพิ่มข้อมูลให้ครบ")
        notebook.add(buy_frame, text="ซื้อ")
        notebook.add(sell_frame, text="ขาย")

        # --- 4. สร้าง widget ภายในแท็บ "รอการเพิ่มข้อมูลให้ครบ" ---
        self.create_waiting_tab_widgets(waiting_frame)

        # --- 5. สร้าง widget ภายในแท็บ "ซื้อ" ---
        self.create_buy_tab_widgets(buy_frame)

        # --- 6. สร้าง widget ภายในแท็บ "ขาย" ---
        self.create_sell_tab_widgets(sell_frame)
        
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
            else:
                entry = ttk.Entry(parent_frame, font=("Helvetica", 12))
                entry.grid(row=i, column=1, padx=(0, 10), pady=8, sticky='ew')

            self.buy_entries[key] = entry

        # --- ทำให้ช่อง 'ราคาต่อหน่วย' ไม่สามารถแก้ไขได้ ---
        # 1. สร้าง Style สำหรับช่องกรอกที่ถูก disable
        style = ttk.Style(parent_frame)
        # กำหนดให้ fieldbackground (พื้นหลังของช่องกรอก) เป็นสีเทา (#f0f0f0) เมื่ออยู่ในสถานะ 'disabled'
        style.map("Disabled.TEntry", fieldbackground=[("disabled", "#f0f0f0")])

        # 2. กำหนด Style และสถานะให้กับช่อง 'price'
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

        # --- เพิ่ม: Label แนะนำการใช้งาน ---
        self.instruction_label = tk.Label(parent_frame, text="ดับเบิ้ลคลิกที่เรคคอร์ดที่ต้องการใส่ข้อมูลให้ครบ", bg="#FAF2E0", fg="blue", font=("Helvetica", 10, "italic"))
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
        self.waiting_tree.tag_configure('buy_waiting', foreground='orange')

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

    def _show_waiting_lot_editor(self, event):
        """แสดงฟอร์มแก้ไขข้อมูลเมื่อมีการดับเบิ้ลคลิก"""
        selected_item = self.waiting_tree.focus()
        if not selected_item:
            return

        # ซ่อนตารางและแสดงฟอร์มแก้ไข
        self.tree_frame.grid_remove()
        self.instruction_label.grid_remove() # ซ่อน Label แนะนำ
       
        self.waiting_editor_frame.grid()
    

        # ดึงข้อมูลจากแถวที่เลือกมาใส่ในฟอร์ม
        record_values = self.waiting_tree.item(selected_item, "values")
        keys = ('lot_number', 'symbol', 'date', 'volume', 'price_per_unit', 'amount', 'status')
        for key, value in zip(keys, record_values):
            self.waiting_editor_entries[key].delete(0, tk.END)
            self.waiting_editor_entries[key].insert(0, value)
            volume = self.waiting_editor_entries['volume'].get()
            amount = self.waiting_editor_entries['amount'].get()


       

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
        # ทำให้  ช่อง  ราคาขาย   และ  ค่า คอมมิชชั้ัั่นเป็น  disabled  เมื่อไม่มีการกรอกข้อมูล
        style = ttk.Style(sell_info_frame)
        style.map("Disabled.TEntry", fieldbackground=[("disabled", "#f0f0f0")])
        self.sell_entries['sell_price'].config(style="Disabled.TEntry", state='disabled')
        self.sell_entries['sell_commission'].config(style="Disabled.TEntry", state='disabled')

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
                    SELECT lot_id, lot_number, buy_date, remaining_volume
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
                    lot_id, lot_number, buy_date, remaining_volume = lot
                    display_text = f"Lot: {lot_number} | ซื้อ: {buy_date} | เหลือ: {remaining_volume:,} หุ้น"
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
                            total_shares = int(vol_field.replace(',', ''))
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
        month = buy_date.split('-')[1]
        day = buy_date.split('-')[2]   
        date_to_rec = f"{year}{month.zfill(2)}{day.zfill(2)}"  # เติมวัน     
      
        # ค้นหา lot_number ล่าสุดสำหรับหุ้นและปีนั้นๆ
        cursor.execute(
            "SELECT lot_number FROM waiting_lots WHERE symbol = ? AND lot_number LIKE ? ORDER BY lot_number DESC LIMIT 1",
            (symbol, f"{symbol}-{date_to_rec}-%")
        )
        last_lot = cursor.fetchone()
        print("symbol:", symbol,f"{symbol}-{year}-%")
        print("Last lot:", last_lot)
        if last_lot:
            # ถ้ามีอยู่แล้ว, ดึงเลขลำดับสุดท้ายมา +1
            last_seq = int(last_lot[0].split('-')[2])
            print(last_seq)
            new_seq = last_seq + 1
        else:
            # ถ้ายังไม่มี, เริ่มนับที่ 1
            new_seq = 1
        
        return f"{symbol}-{date_to_rec}-{new_seq:03d}" # format ให้เป็นเลข 3 หลัก เช่น 001, 002

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
                    # จัดรูปแบบตัวเลขก่อนแสดงผล
                    formatted_record = list(record)
                    formatted_record[3] = f"{record[3]:,.4f}" # volume
                    formatted_record[4] = f"{record[4]:,.4f}" # price
                    formatted_record[5] = f"{record[5]:,.2f}" # amount
                    self.waiting_tree.insert('', 'end', values=formatted_record, tags=('buy_waiting',))
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
                    lot_number = self._generate_lot_number(cursor, symbol, date)
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
                sell_volume = int(vol_str.replace(',', ''))
            except ValueError:
                messagebox.showerror("ข้อมูลไม่ถูกต้อง", "กรุณากรอกจำนวนหุ้นเป็นตัวเลข", parent=self)
                return

            lot_info = next((l for l in self.open_lots_list if l['lot_id'] == selected_lot_ids[0]), None)
            if not lot_info:
                messagebox.showerror("เกิดข้อผิดพลาด", "ไม่พบข้อมูลล็อตที่เลือก", parent=self)
                return
            if sell_volume <= 0 or sell_volume > lot_info['remaining_volume']:
                messagebox.showerror("จำนวนหุ้นไม่ถูกต้อง", f"จำนวนหุ้นที่ขายต้องมากกว่า 0 และไม่เกิน {lot_info['remaining_volume']:,}", parent=self)
                return

            sale_plan.append({'lot_id': lot_info['lot_id'], 'sell_volume': sell_volume, 'remaining_volume': lot_info['remaining_volume']})
        else:
            # หลายล็อต ต้องขายทั้งล็อต
            for lid in selected_lot_ids:
                lot_info = next((l for l in self.open_lots_list if l['lot_id'] == lid), None)
                if not lot_info:
                    messagebox.showerror("เกิดข้อผิดพลาด", "ไม่พบข้อมูลล็อตที่เลือก", parent=self)
                    return
                sale_plan.append({'lot_id': lot_info['lot_id'], 'sell_volume': lot_info['remaining_volume'], 'remaining_volume': lot_info['remaining_volume']})

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

        # บันทึกลงฐานข้อมูล
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
                    """, (lid, sell_date, vol, sell_price, assigned_tax))

                    # อัปเดต remaining_volume และ status
                    cursor.execute("SELECT remaining_volume FROM lots WHERE lot_id = ?", (lid,))
                    row = cursor.fetchone()
                    if not row:
                        continue
                    new_remaining = row[0] - vol
                    new_status = 'CLOSED' if new_remaining == 0 else 'OPEN'
                    cursor.execute("UPDATE lots SET remaining_volume = ?, status = ? WHERE lot_id = ?", (new_remaining, new_status, lid))

                conn.commit()

            messagebox.showinfo("สำเร็จ", f"บันทึกการขายเรียบร้อยแล้ว", parent=self)
            self.clear_sell_entries()
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
        self.sell_symbol_entry['values'] = self.get_holding_symbols()

    def _show_waiting_lot_summary(self):
        """แสดงข้อมูลสรุปจากฟอร์มแก้ไข"""
        try:
            print("Debug 1: Starting get 'lot_number'") # Debug Line
            lot_number = self.waiting_editor_entries['lot_number'].get().strip()
            
            print("Debug 2: Starting get 'symbol'") # Debug Line
            symbol = self.waiting_editor_entries['symbol'].get().strip().upper()
            
            print("Debug 3: Starting get 'date'") # Debug Line
            date = self.waiting_editor_entries['date'].get().strip()
            volume_str = self.waiting_editor_entries['volume'].get().strip() or '0'
            # ⚠️ NEW: ลบเครื่องหมายจุลภาคออกก่อน
            volume_str = volume_str.replace('\u200b', '').replace('\xa0', '').replace(',', '')
            price_str = self.waiting_editor_entries['price_per_unit'].get().strip() or '0'
            amount_str = self.waiting_editor_entries['amount'].get().strip() or '0'
            # ⚠️ NEW: ลบเครื่องหมายจุลภาคออกก่อน
            amount_str = amount_str.replace('\u200b', '').replace('\xa0', '').replace(',', '')
            
            # (โค้ดแปลงค่า float ที่เคยให้ไปในการทดลองก่อนหน้า)
            volume = float(volume_str)
            price = float(price_str)
            amount = float(amount_str)

            price = amount/volume 

            summary_message = (
                f"ข้อมูลสรุป:\n\n"
                f"ล็อตหมายเลข: {lot_number}\n"
                f"กองทุน: {symbol}\n"
                f"วันที่: {date}\n"
                f"จำนวน: {volume:,} หน่วย\n"
                f"ราคา: {price:,.2f} บาท/หน่วย\n"
                f"จำนวนเงินที่จ่าย: {amount:,.2f} บาท\n\n"
            )
            # 5. แสดงกล่องข้อความยืนยัน
            if messagebox.askokcancel("ยืนยันข้อมูล", summary_message, parent=self):
                self._save_waiting_lot_data(lot_number, symbol, date, volume, price, amount)
        except (ValueError, TypeError):
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "กรุณาตรวจสอบข้อมูลในฟอร์มให้ถูกต้อง", parent=self)    
        except ZeroDivisionError:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "จำนวนหน่วยต้องมากกว่า 0", parent=self)

    def _save_waiting_lot_data(self, lot_number, symbol, date, volume, price, amount):
        """บันทึกข้อมูลจากฟอร์มแก้ไขลงฐานข้อมูล"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO lots (lot_number, symbol, buy_date, buy_volume, buy_price_per_unit, status,remaining_volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (lot_number, symbol, date, volume, price, 'OPEN', volume))
                conn.commit()
                #ลยข้อมูลออกจากตาราง waiting_lots
                cursor.execute("DELETE FROM waiting_lots WHERE lot_number = ?", (lot_number,))
                conn.commit()
            messagebox.showinfo("สำเร็จ", f"บันทึกข้อมูลล็อตรอซื้อเรียบร้อยแล้ว", parent=self)
            self._hide_waiting_lot_editor()
            self._load_waiting_lots_data()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}", parent=self)
    def _hide_waiting_lot_editor(self):
        """ซ่อนฟอร์มแก้ไขและกลับไปแสดงตาราง"""
        self.waiting_editor_frame.grid_remove()
        self.instruction_label.grid() # แสดง Label แนะนำอีกครั้ง
        self.tree_frame.grid()
            

if __name__ == "__main__":
    app = Tran_app()
    app.mainloop()