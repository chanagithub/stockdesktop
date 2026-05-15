import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import chmodule
import sqlite3
from tkcalendar import DateEntry # นำเข้าโดยตรง

class DividendReturnApp(tk.Toplevel):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db_path = db_path
        self.lot_checkboxes = [] # สำหรับเก็บ Checkbox ของล็อต
        self.return_lot_checkboxes = [] # สำหรับแท็บคืนทุน
        self._dividend_lots_key = None
        self._return_lots_key = None
        self.title(f"บันทึกปันผล/คืนทุน - {os.path.basename(db_path)}")
        chmodule.ChClass.setwindowcenter(self, 600, 650) # 1. เพิ่มความสูงหน้าต่าง

        # --- ตั้งค่าไอคอน (ถ้ามี) ---
        try:
            icon_image = tk.PhotoImage(file=chmodule.ChClass.get_resource_path('Graph.png'))
            self.iconphoto(True, icon_image)
        except tk.TclError:
            print("ไม่พบไฟล์ไอคอน 'Graph.png'")

        self.create_widgets()

        # --- ทำให้หน้าต่างอยู่บนสุด ---
        self.lift() # นำหน้าต่างขึ้นมาบนสุด
        self.focus_force() # ให้ focus กับหน้าต่างนี้
        self.attributes('-topmost', True) # ตั้งค่าให้อยู่บนสุดเสมอ
        self.after(200, lambda: self.attributes('-topmost', False)) # ยกเลิกหลังจาก 200ms

    def create_widgets(self):
        # --- สร้าง Notebook (Tab control) ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # --- ตั้งค่า Style สำหรับ Tab ---
        style = ttk.Style(self)
        style.configure('TFrame', background='white')
        # สีม่วงอ่อน (Lavender)
        style.configure('LightPurple.TFrame', background="#E6E6FA")
        # สีเขียวอ่อน
        style.configure('LightGreen.TFrame', background="#DFF0D8")

        # --- ตั้งค่า Style สำหรับ Label ภายใน Tab ---
        # ให้ Label มีพื้นหลังสีเดียวกับ Frame ที่มันอยู่
        style.configure('LightPurple.TLabel', background="#E6E6FA")
        style.configure('LightGreen.TLabel', background="#DFF0D8")

        # 1. แก้ไข Style ของ Combobox ให้มีพื้นหลังสีม่วงอ่อน
        style.map('TCombobox', fieldbackground=[('!disabled', '#E6E6FA')])
        style.map('TCombobox', selectbackground=[('!disabled', '#E6E6FA')])
        style.map('TCombobox', selectforeground=[('!disabled', 'black')])
        
        # 2. เพิ่ม Style สำหรับ Checkbutton และ LabelFrame เพื่อให้มีสีพื้นหลังที่ถูกต้อง
        style.configure('LightPurple.TCheckbutton', background='#E6E6FA')
        style.configure('LightPurple.TLabelframe', background='#E6E6FA')
        style.configure('LightPurple.TLabelframe.Label', background='#E6E6FA')

        style.configure('LightGreen.TCheckbutton', background='#DFF0D8')
        style.configure('LightGreen.TLabelframe', background='#DFF0D8')
        style.configure('LightGreen.TLabelframe.Label', background='#DFF0D8')

        # --- สร้าง Tab สำหรับเงินปันผล ---
        self.dividend_tab = ttk.Frame(self.notebook, style='LightPurple.TFrame')
        self.notebook.add(self.dividend_tab, text="  บันทึกเงินปันผล  ")
        self.create_dividend_widgets()

        # --- สร้าง Tab สำหรับเงินคืนทุน ---
        self.return_tab = ttk.Frame(self.notebook, style='LightGreen.TFrame')
        self.notebook.add(self.return_tab, text="  บันทึกเงินคืนทุน  ")
        self.create_return_widgets()

    def create_dividend_widgets(self):
        """สร้าง Widgets ภายในแท็บเงินปันผล"""
        # สร้าง tk.Frame ซ้อนข้างในเพื่อกำหนดสี background ที่แน่นอน
        bg_frame = tk.Frame(self.dividend_tab, bg="#E6E6FA") # สีม่วงอ่อน
        bg_frame.pack(expand=True, fill="both")
        
        # --- สร้าง Frame หลักสำหรับจัดวาง Widget ---
        # เปลี่ยนจาก ttk.Frame เป็น tk.Frame และกำหนดสีโดยตรงเพื่อแก้ปัญหาสีเทา
        main_frame = tk.Frame(bg_frame, bg="#E6E6FA")
        main_frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        # --- แถวที่ 1: ชื่อหุ้น ---
        tk.Label(main_frame, text="ชื่อหุ้น (Symbol):", bg="#E6E6FA").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.stock_symbol_combo = ttk.Combobox(main_frame, state="readonly")
        self.stock_symbol_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        # 2. เมื่อเลือกหุ้น ให้ดึงข้อมูลล็อต
        self.stock_symbol_combo.bind("<<ComboboxSelected>>", self.populate_lots_for_selected_stock)
        # โหลดรายชื่อหุ้นทั้งหมด
        self.load_stock_symbols()

        # 3. ดึงข้อมูลล็อตเมื่อกด Enter ใน Combobox
        self.stock_symbol_combo.bind("<Return>", self.populate_lots_for_selected_stock)

        # --- แถวที่ 2: วันที่จ่ายปันผล ---
        tk.Label(main_frame, text="วันที่จ่ายปันผล:", bg="#E6E6FA").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        # 3. เปลี่ยนเป็น Date Picker
        self.dividend_date_entry = DateEntry(main_frame, date_pattern='yyyy-mm-dd', width=18)
        self.dividend_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(main_frame, text="Record/XD date:", bg="#E6E6FA").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.dividend_record_date_entry = DateEntry(main_frame, date_pattern='yyyy-mm-dd', width=18)
        self.dividend_record_date_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.dividend_record_date_entry.bind("<<DateEntrySelected>>", self.populate_lots_for_selected_stock)
        self.dividend_record_date_entry.bind("<FocusOut>", self.populate_lots_for_selected_stock)

        # --- แถวที่ 3: จำนวนเงินปันผล ---
        tk.Label(main_frame, text="จำนวนเงินปันผล (บาท/หุ้น):", bg="#E6E6FA").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.dividend_amount_entry = ttk.Entry(main_frame)
        self.dividend_amount_entry.bind("<KeyRelease>", self._calculate_net_dividend)
        self.dividend_amount_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        # --- แถวที่ 4: อัตราภาษี ---
        tk.Label(main_frame, text="อัตราภาษี (%):", bg="#E6E6FA").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.tax_rate_entry = ttk.Entry(main_frame)
        self.tax_rate_entry.bind("<KeyRelease>", self._calculate_net_dividend)
        self.tax_rate_entry.insert(0, "10") # 4. ใส่ค่า default 10%
        self.tax_rate_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        # --- แถวที่ 5: จำนวนเงินที่จะได้รับ ---
        tk.Label(main_frame, text="เงินปันผลสุทธิ (บาท):", bg="#E6E6FA").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.net_dividend_label = tk.Label(main_frame, text="0.00", bg="#E6E6FA", font=("Helvetica", 12, "bold"))
        self.net_dividend_label.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        
        # --- แถวที่ 6: พื้นที่สำหรับเลือกล็อต ---
        lot_frame = tk.LabelFrame(main_frame, text="  เลือกล็อตที่ได้รับปันผล  ", bg="#E6E6FA", fg="black")
        lot_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")
        
        # --- Checkbox "เลือกล็อตทั้งหมด" ---
        self.select_all_var = tk.BooleanVar()
        select_all_check = ttk.Checkbutton(lot_frame, text="เลือกล็อตทั้งหมด", variable=self.select_all_var, style='LightPurple.TCheckbutton', command=self.toggle_select_all_lots)
        select_all_check.pack(anchor="w", padx=5, pady=(5,0))

        # --- สร้าง Frame พร้อม Scrollbar สำหรับแสดงรายการ Checkbox ของแต่ละล็อต ---
        lot_list_canvas = tk.Canvas(lot_frame, bg="#E6E6FA", highlightthickness=0) # bg ของ Canvas
        scrollbar = ttk.Scrollbar(lot_frame, orient="vertical", command=lot_list_canvas.yview)
        self.scrollable_frame = tk.Frame(lot_list_canvas, bg="#E6E6FA")
        
        # กำหนดให้ main_frame ขยายตาม lot_frame
        main_frame.grid_rowconfigure(6, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: lot_list_canvas.configure(scrollregion=lot_list_canvas.bbox("all"))
        )

        lot_list_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        lot_list_canvas.configure(yscrollcommand=scrollbar.set)

        lot_list_canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        # --- ปุ่มบันทึกข้อมูล ---
        save_button = ttk.Button(main_frame, text="บันทึกข้อมูลปันผล", command=self.save_dividend_data)
        save_button.grid(row=7, column=0, columnspan=2, pady=(15, 5), sticky="ew")

    def create_return_widgets(self):
        """สร้าง Widgets ภายในแท็บเงินคืนทุน"""
        # สร้าง tk.Frame ซ้อนข้างในเพื่อกำหนดสี background ที่แน่นอน
        bg_frame = tk.Frame(self.return_tab, bg="#DFF0D8")
        bg_frame.pack(expand=True, fill="both")

        main_frame = tk.Frame(bg_frame, bg="#DFF0D8")
        main_frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        # --- ชื่อหุ้น ---
        tk.Label(main_frame, text="ชื่อหุ้น (Symbol):", bg="#DFF0D8").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.return_stock_symbol_combo = ttk.Combobox(main_frame, state="readonly", values=self.stock_symbol_combo['values'])
        self.return_stock_symbol_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.return_stock_symbol_combo.bind("<<ComboboxSelected>>", self.populate_lots_for_return_tab)
        self.return_stock_symbol_combo.bind("<Return>", self.populate_lots_for_return_tab)

        # --- วันที่คืนทุน ---
        tk.Label(main_frame, text="วันที่คืนทุน:", bg="#DFF0D8").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.return_date_entry = DateEntry(main_frame, date_pattern='yyyy-mm-dd', width=18)
        self.return_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(main_frame, text="Record/XD date:", bg="#DFF0D8").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.return_record_date_entry = DateEntry(main_frame, date_pattern='yyyy-mm-dd', width=18)
        self.return_record_date_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.return_record_date_entry.bind("<<DateEntrySelected>>", self.populate_lots_for_return_tab)
        self.return_record_date_entry.bind("<FocusOut>", self.populate_lots_for_return_tab)

        # --- จำนวนเงินคืนทุน ---
        tk.Label(main_frame, text="จำนวนเงินคืนทุน (บาท/หุ้น):", bg="#DFF0D8").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.return_amount_entry = ttk.Entry(main_frame)
        self.return_amount_entry.bind("<KeyRelease>", self._calculate_total_return)
        self.return_amount_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # --- จำนวนเงินที่จะได้รับ ---
        tk.Label(main_frame, text="เงินคืนทุนรวม (บาท):", bg="#DFF0D8").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.total_return_label = tk.Label(main_frame, text="0.00", bg="#DFF0D8", font=("Helvetica", 12, "bold"))
        self.total_return_label.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        # --- พื้นที่สำหรับเลือกล็อต ---
        lot_frame = tk.LabelFrame(main_frame, text="  เลือกล็อตที่ได้รับเงินคืนทุน  ", bg="#DFF0D8", fg="black")
        lot_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")

        self.return_select_all_var = tk.BooleanVar()
        select_all_check = ttk.Checkbutton(lot_frame, text="เลือกล็อตทั้งหมด", variable=self.return_select_all_var, style='LightGreen.TCheckbutton', command=self.toggle_select_all_return_lots)
        select_all_check.pack(anchor="w", padx=5, pady=(5,0))

        lot_list_canvas = tk.Canvas(lot_frame, bg="#DFF0D8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(lot_frame, orient="vertical", command=lot_list_canvas.yview)
        self.return_scrollable_frame = tk.Frame(lot_list_canvas, bg="#DFF0D8")

        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        self.return_scrollable_frame.bind(
            "<Configure>",
            lambda e: lot_list_canvas.configure(scrollregion=lot_list_canvas.bbox("all"))
        )

        lot_list_canvas.create_window((0, 0), window=self.return_scrollable_frame, anchor="nw")
        lot_list_canvas.configure(yscrollcommand=scrollbar.set)

        lot_list_canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        # --- ปุ่มบันทึกข้อมูล ---
        save_button = ttk.Button(main_frame, text="บันทึกข้อมูลเงินคืนทุน", command=self.save_return_data)
        save_button.grid(row=6, column=0, columnspan=2, pady=(15, 5), sticky="ew")

    def load_stock_symbols(self):
        """ดึงรายชื่อหุ้นทั้งหมด (ไม่ซ้ำ) จากตาราง lots และใส่ใน Combobox"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT symbol FROM lots ORDER BY symbol")
            symbols = [row[0] for row in cursor.fetchall()]
            self.stock_symbol_combo['values'] = symbols
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถดึงรายชื่อหุ้นได้: {e}")

    def _fetch_eligible_lots(self, symbol, record_date):
        """Return lots eligible on the record/XD date, including closed lots sold after it."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    l.lot_number,
                    l.buy_date,
                    CASE
                        WHEN l.status = 'OPEN' THEN l.remaining_volume
                        ELSE COALESCE(s.sell_volume, l.buy_volume)
                    END AS eligible_volume,
                    l.buy_price_per_unit,
                    l.status,
                    s.sell_date
                FROM lots l
                LEFT JOIN sales s ON s.lot_id = l.lot_number
                WHERE l.symbol = ?
                  AND l.buy_date <= ?
                  AND (
                      (l.status = 'OPEN' AND l.remaining_volume > 0)
                      OR
                      (l.status = 'CLOSE' AND s.sell_date > ?)
                  )
                ORDER BY l.buy_date, l.lot_number
            """, (symbol, record_date, record_date))
            return cursor.fetchall()

    def populate_lots_for_selected_stock(self, event=None):
        """ดึงข้อมูลล็อตที่ยังถือครองของหุ้นที่เลือก และสร้าง Checkbox"""
        selected_symbol = self.stock_symbol_combo.get()

        if not selected_symbol:
            return

        record_date = self.dividend_record_date_entry.get_date().strftime('%Y-%m-%d')
        lots_key = (selected_symbol, record_date)
        if lots_key == self._dividend_lots_key and self.lot_checkboxes:
            return

        # ล้าง Checkbox ของล็อตเก่าออกก่อน
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.lot_checkboxes.clear()

        try:
            active_lots = self._fetch_eligible_lots(selected_symbol, record_date)

            if not active_lots:
                tk.Label(self.scrollable_frame, text="ไม่พบข้อมูลล็อตที่ยังถือครอง", bg="#E6E6FA").pack(pady=10)
                return

            for lot in active_lots:
                lot_number, date, remaining_volume, buy_price_per_unit, status, sell_date = lot
                # แก้ไข: แสดงข้อความเริ่มต้นโดยไม่มีราคาซื้อ
                status_text = "OPEN" if status == "OPEN" else f"SOLD {sell_date}"
                lot_text = f"Lot: {lot_number} | {date} | {remaining_volume:,.0f} หุ้น | {status_text}"
                var = tk.BooleanVar()
                # เมื่อคลิก Checkbox ให้คำนวณใหม่
                cb = ttk.Checkbutton(self.scrollable_frame, text=lot_text, variable=var, style='LightPurple.TCheckbutton', command=self._calculate_net_dividend)
                cb.pack(anchor="w", padx=10, pady=2)
                # แก้ไข: เก็บ widget ของ checkbox, lot_number, และข้อมูลอื่นๆ เพื่อใช้อัปเดตข้อความ
                self.lot_checkboxes.append({'widget': cb, 'lot_id': lot_number, 'date': date, 'shares': remaining_volume, 'status_text': status_text, 'var': var})
            self._dividend_lots_key = lots_key
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถดึงข้อมูลล็อตได้: {e}")
        
        # คำนวณยอดเงินเมื่อโหลดข้อมูลล็อตเสร็จ
        self._calculate_net_dividend()

    def toggle_select_all_lots(self):
        """เลือก หรือ ยกเลิกการเลือก Checkbox ของล็อตทั้งหมด"""
        is_selected = self.select_all_var.get()
        for item in self.lot_checkboxes:
            item['var'].set(is_selected)
        # คำนวณยอดเงินเมื่อกด Select All
        self._calculate_net_dividend()

    def populate_lots_for_return_tab(self, event=None):
        """ดึงข้อมูลล็อตสำหรับแท็บคืนทุน"""
        selected_symbol = self.return_stock_symbol_combo.get()
        if not selected_symbol: return

        record_date = self.return_record_date_entry.get_date().strftime('%Y-%m-%d')
        lots_key = (selected_symbol, record_date)
        if lots_key == self._return_lots_key and self.return_lot_checkboxes:
            return

        for widget in self.return_scrollable_frame.winfo_children():
            widget.destroy()
        self.return_lot_checkboxes.clear()

        try:
            active_lots = self._fetch_eligible_lots(selected_symbol, record_date)

            if not active_lots:
                tk.Label(self.return_scrollable_frame, text="ไม่พบข้อมูลล็อตที่ยังถือครอง", bg="#DFF0D8").pack(pady=10)
                return

            for lot in active_lots:
                lot_number, date, remaining_volume, buy_price_per_unit, status, sell_date = lot
                # แก้ไข: แสดงข้อความเริ่มต้นโดยไม่มีราคาซื้อ
                status_text = "OPEN" if status == "OPEN" else f"SOLD {sell_date}"
                lot_text = f"Lot: {lot_number} | {date} | {remaining_volume:,.0f} หุ้น | {status_text}"
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(self.return_scrollable_frame, text=lot_text, variable=var, style='LightGreen.TCheckbutton', command=self._calculate_total_return)
                cb.pack(anchor="w", padx=10, pady=2)
                # แก้ไข: เก็บ widget และข้อมูลอื่นๆ เพื่อใช้อัปเดตข้อความ
                self.return_lot_checkboxes.append({'widget': cb, 'lot_id': lot_number, 'date': date, 'shares': remaining_volume, 'status_text': status_text, 'var': var})
            self._return_lots_key = lots_key

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถดึงข้อมูลล็อตได้: {e}")
        self._calculate_total_return()

    def _calculate_net_dividend(self, event=None):
        """คำนวณและอัปเดต Label เงินปันผลสุทธิ"""
        try:
            # 1. ดึงค่าจาก input fields
            dividend_per_share = float(self.dividend_amount_entry.get() or 0)
            tax_rate = float(self.tax_rate_entry.get() or 0)

            # 2. คำนวณจำนวนหุ้นทั้งหมดที่ถูกเลือก และอัปเดตข้อความของแต่ละ Checkbox
            total_selected_shares = 0
            for item in self.lot_checkboxes:
                # คำนวณเงินปันผลสำหรับล็อตนี้
                dividend_for_lot = item['shares'] * dividend_per_share
                # สร้างข้อความใหม่
                new_text = f"Lot: {item['lot_id']} | {item['date']} | {item['shares']:,.0f} หุ้น | {item.get('status_text', '')} | ปันผล: {dividend_for_lot:,.2f} บาท"
                # อัปเดตข้อความบน Checkbox
                item['widget'].config(text=new_text)

                if item['var'].get(): # ถ้า Checkbox ถูกเลือก
                    total_selected_shares += item['shares']
            
            # 3. คำนวณเงินปันผล
            gross_dividend = total_selected_shares * dividend_per_share
            tax_amount = gross_dividend * (tax_rate / 100)
            net_dividend = gross_dividend - tax_amount

            # 4. อัปเดต Label
            self.net_dividend_label.config(text=f"{net_dividend:,.2f} บาท (จาก {total_selected_shares:,.0f} หุ้น)")

        except (ValueError, TypeError):
            # ถ้าผู้ใช้กรอกข้อมูลที่ไม่ใช่ตัวเลข
            self.net_dividend_label.config(text="ข้อมูลไม่ถูกต้อง")

    def toggle_select_all_return_lots(self):
        """เลือก หรือ ยกเลิกการเลือก Checkbox ของล็อตทั้งหมดในแท็บคืนทุน"""
        is_selected = self.return_select_all_var.get()
        for item in self.return_lot_checkboxes:
            item['var'].set(is_selected)
        self._calculate_total_return()

    def _calculate_total_return(self, event=None):
        """คำนวณและอัปเดต Label เงินคืนทุนรวม"""
        try:
            amount_per_share = float(self.return_amount_entry.get() or 0)

            total_selected_shares = 0
            for item in self.return_lot_checkboxes:
                # คำนวณเงินคืนทุนสำหรับล็อตนี้
                return_for_lot = item['shares'] * amount_per_share
                # สร้างข้อความใหม่
                new_text = f"Lot: {item['lot_id']} | {item['date']} | {item['shares']:,.0f} หุ้น | {item.get('status_text', '')} | คืนทุน: {return_for_lot:,.2f} บาท"
                # อัปเดตข้อความบน Checkbox
                item['widget'].config(text=new_text)

                if item['var'].get(): # ถ้า Checkbox ถูกเลือก
                    total_selected_shares += item['shares']

            total_return = total_selected_shares * amount_per_share
            # แก้ไข: อัปเดต Label ให้แสดงจำนวนหุ้นด้วย
            self.total_return_label.config(text=f"{total_return:,.2f} บาท (จาก {total_selected_shares:,.0f} หุ้น)")

        except (ValueError, TypeError):
            self.total_return_label.config(text="ข้อมูลไม่ถูกต้อง")

    def save_dividend_data(self):
        """รวบรวมข้อมูลและบันทึกลงในตาราง dividends"""
        try:
            # --- 1. รวบรวมและตรวจสอบข้อมูลจากฟอร์ม ---
            dividend_date = self.dividend_date_entry.get_date().strftime('%Y-%m-%d')
            dividend_per_share = float(self.dividend_amount_entry.get())
            tax_rate = float(self.tax_rate_entry.get())

            selected_lots = [item for item in self.lot_checkboxes if item['var'].get()]

            if not self.stock_symbol_combo.get():
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณาเลือกหุ้น")
                return
            if not selected_lots:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณาเลือกล็อตที่ได้รับปันผลอย่างน้อย 1 ล็อต")
                return
            if dividend_per_share <= 0:
                messagebox.showwarning("ข้อมูลไม่ถูกต้อง", "กรุณากรอกจำนวนเงินปันผลต่อหุ้นให้ถูกต้อง")
                return

            # --- 2. เตรียมข้อมูลที่จะบันทึกสำหรับแต่ละล็อต ---
            records_to_insert = []
            for lot in selected_lots:
                lot_id = lot['lot_id']
                shares = lot['shares']
                
                # คำนวณสำหรับแต่ละล็อต
                gross_dividend_for_lot = shares * dividend_per_share
                tax_for_lot = gross_dividend_for_lot * (tax_rate / 100)
                
                records_to_insert.append((lot_id, dividend_date, gross_dividend_for_lot, tax_for_lot)) # เพิ่ม lot_id อีกครั้งสำหรับ lot_number

            # --- 3. บันทึกข้อมูลลงฐานข้อมูล ---
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ใช้ transaction เพื่อให้แน่ใจว่าข้อมูลทั้งหมดจะถูกบันทึกพร้อมกัน (แก้ไข INSERT statement)
            cursor.executemany("""
                INSERT INTO dividends (lot_id, payment_date, amount, tax)
                VALUES (?, ?, ?, ?)
            """, records_to_insert)
            
            conn.commit()
            conn.close()

            messagebox.showinfo("สำเร็จ", f"บันทึกข้อมูลเงินปันผลจำนวน {len(records_to_insert)} รายการเรียบร้อยแล้ว")
            self.destroy() # ปิดหน้าต่างหลังบันทึกสำเร็จ

        except (ValueError, TypeError):
            messagebox.showerror("เกิดข้อผิดพลาด", "ข้อมูลบางอย่างไม่ถูกต้อง (เช่น จำนวนเงินหรืออัตราภาษี)\nกรุณาตรวจสอบและลองอีกครั้ง")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถบันทึกข้อมูลได้: {e}")

    def save_return_data(self):
        """รวบรวมข้อมูลและบันทึกลงในตาราง capital_returns"""
        try:
            payment_date = self.return_date_entry.get_date().strftime('%Y-%m-%d')
            amount_per_share = float(self.return_amount_entry.get())

            selected_lots = [item for item in self.return_lot_checkboxes if item['var'].get()]

            if not self.return_stock_symbol_combo.get():
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณาเลือกหุ้น")
                return
            if not selected_lots:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณาเลือกล็อตที่ได้รับเงินคืนทุนอย่างน้อย 1 ล็อต")
                return
            if amount_per_share <= 0:
                messagebox.showwarning("ข้อมูลไม่ถูกต้อง", "กรุณากรอกจำนวนเงินคืนทุนต่อหุ้นให้ถูกต้อง")
                return

            records_to_insert = []
            for lot in selected_lots:
                lot_id = lot['lot_id']
                shares = lot['shares']
                amount_for_lot = shares * amount_per_share
                records_to_insert.append((lot_id, payment_date, amount_for_lot)) # เพิ่ม lot_id อีกครั้งสำหรับ lot_number

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO capital_returns (lot_id, payment_date, amount)
                VALUES (?, ?, ?)
            """, records_to_insert)
            conn.commit()
            conn.close()

            messagebox.showinfo("สำเร็จ", f"บันทึกข้อมูลเงินคืนทุนจำนวน {len(records_to_insert)} รายการเรียบร้อยแล้ว")
            self.destroy()
        except (ValueError, TypeError):
            messagebox.showerror("เกิดข้อผิดพลาด", "ข้อมูลบางอย่างไม่ถูกต้อง (เช่น จำนวนเงิน)\nกรุณาตรวจสอบและลองอีกครั้ง")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถบันทึกข้อมูลได้: {e}")

if __name__ == "__main__":
    # ตรวจสอบว่ามีการส่ง argument (path ของ database) มาหรือไม่
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        if os.path.exists(db_path):
            app = DividendReturnApp(db_path)
            app.mainloop()
        else:
            messagebox.showerror("เกิดข้อผิดพลาด", f"ไม่พบไฟล์ฐานข้อมูลที่:\n{db_path}")
    else:
        messagebox.showerror("เกิดข้อผิดพลาด", "ไม่ได้ระบุไฟล์ฐานข้อมูล\nกรุณาเปิดโปรแกรมนี้ผ่านหน้าต่างหลัก")
