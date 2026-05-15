import tkinter as tk
from tkinter import font as tkfont, messagebox
from tkinter import ttk
import sys
import os
import subprocess  
import chmodule
import sqlite3
from datetime import datetime # เพิ่มการนำเข้า datetime
from collections import defaultdict # Import defaultdict for easier grouping

class StockAnalyzeApp(tk.Toplevel):
    def __init__(self, parent, db_path):
        super().__init__(parent)
         # --- เพิ่มโค้ดตั้งค่าไอคอน ---
        try:
            self.icon_image = tk.PhotoImage(file=chmodule.ChClass.get_resource_path('Graph.png'))
            self.iconphoto(True, self.icon_image)
        except tk.TclError:
            print("ไม่พบไฟล์ไอคอน 'Graph.png' ใน transaction.py")
        self.db_path = db_path

        self.title("Stock Analyze Application")
        chmodule.ChClass.setwindowcenter(self, 1300, 700) # ใช้ขนาด 600x400 ตามที่เคยกำหนด
        self.attributes("-topmost", True)  # ตั้งให้หน้าต่างอยู่ด้านบนสุด

        # --- สร้างและกำหนดค่า Style ---
        style = ttk.Style(self)
        style.theme_use('default') # สามารถเปลี่ยนเป็น 'clam', 'alt', 'default', 'classic'

        # กำหนดค่าพื้นฐานของสไตล์แท็บ
        style.configure('TNotebook.Tab', padding=[10, 2])

        # สร้าง Notebook (Tab control)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        # --- สร้าง Frame สำหรับแต่ละแท็บ ---
        # แท็บที่ 1: หุ้นที่ยังถือครองอยู่
        self.tab1 = tk.Frame(self.notebook, bg='lightcyan')
        self.notebook.add(self.tab1, text='หุ้นที่ยังถือครองอยู่ (unit handling)')
        self.create_tab1_widgets()

        # แท็บที่ 2: หุ้นที่ขายไปแล้ว
        self.tab2 = tk.Frame(self.notebook, bg='lightyellow')
        self.notebook.add(self.tab2, text='หุ้นที่ขายไปแล้ว (closed trade)')
        self.create_tab2_widgets()

        # แท็บที่ 3: เงินปันผล และ เงินคืน
        self.tab3 = tk.Frame(self.notebook, bg= '#FFDDC1') # เปลี่ยนเป็นสีส้มอ่อนลง
        self.notebook.add(self.tab3, text='เงินปันผล และ เงินคืนที่ได้รับ (dividend and capital return)')
        self.create_tab3_widgets()

        # ผูกเหตุการณ์การเปลี่ยนแท็บกับฟังก์ชัน on_tab_changed
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # ผูกเหตุการณ์การเปลี่ยนแท็บกับฟังก์ชัน on_tab_changed
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # ตั้งค่าสีเริ่มต้นสำหรับแท็บแรก
        self.on_tab_changed(None)

    def on_tab_changed(self, event):
        style = ttk.Style()
        selected_tab_index = self.notebook.index(self.notebook.select())
        tab_colors = ['lightcyan', 'lightyellow', '#FFDDC1'] # เปลี่ยนสีให้ตรงกับพื้นหลังของแท็บ
        style.map('TNotebook.Tab', background=[('selected', tab_colors[selected_tab_index])])        
        
    def create_tab1_widgets(self):
        """สร้างวิดเจ็ตสำหรับแท็บที่ 1 (หุ้นที่ถือครอง)"""
        # --- สร้าง Frame หลักสำหรับจัดวาง ---
        container = ttk.Frame(self.tab1, style="lightcyan.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # --- กำหนด Style ให้กับ Treeview ---
        style = ttk.Style()
        # กำหนดสีพื้นหลังของข้อมูลและพื้นที่ว่างให้เป็น lightcyan
        style.configure("Treeview", background="lightcyan", fieldbackground="lightcyan", foreground="black")
        style.configure("Yellow.Treeview", background="lightyellow", fieldbackground="lightyellow", foreground="black")
        style.configure("Orange.Treeview", background="#FFDDC1", fieldbackground="#FFDDC1", foreground="black")

        # --- สร้าง Treeview สำหรับแสดงข้อมูล (เพิ่มคอลัมน์และจัดลำดับใหม่) ---
        columns = ('symbol', 'num_lots', 'total_volume', 'invested_amount', 'total_cost', 'avg_price', 'avg_price_with_returns', 'total_returns')
        # แก้ไข: เปลี่ยน show='headings' เป็น 'tree headings' เพื่อแสดงคอลัมน์สำหรับ tree expander
        self.open_lots_tree = ttk.Treeview(container, columns=columns, show='tree headings')

        # --- กำหนด Header และความกว้างของคอลัมน์ ---
        # กำหนดค่าให้คอลัมน์ #0 (คอลัมน์ของ tree)
        self.open_lots_tree.heading('#0', text='') # ไม่ต้องมีหัวข้อ
        self.open_lots_tree.column('#0', width=20, stretch=tk.NO, anchor=tk.CENTER) # กำหนดความกว้างให้น้อยๆ

        self.open_lots_tree.heading('symbol', text='ชื่อหุ้น / Lot Number') # Updated header
        self.open_lots_tree.heading('num_lots', text='จำนวนล็อต / วันที่ซื้อ') # Updated header
        self.open_lots_tree.heading('total_volume', text='จำนวนหุ้นรวม / จำนวนที่ซื้อ') # Updated header
        self.open_lots_tree.heading('invested_amount', text='เงินลงทุน')
        self.open_lots_tree.heading('total_cost', text='มูลค่าต้นทุนรวม / คงเหลือ')
        self.open_lots_tree.heading('avg_price', text='เฉลี่ย/หุ้น')
        self.open_lots_tree.heading('avg_price_with_returns', text='เฉลี่ยรวมปันผล/หุ้น') # คอลัมน์ใหม่
        self.open_lots_tree.heading('total_returns', text='ปันผล+เงินคืน')

        self.open_lots_tree.column('symbol', width=120, anchor=tk.W)
        self.open_lots_tree.column('num_lots', width=110, anchor=tk.CENTER)
        self.open_lots_tree.column('total_volume', width=110, anchor=tk.E)
        self.open_lots_tree.column('invested_amount', width=130, anchor=tk.E)
        self.open_lots_tree.column('total_cost', width=130, anchor=tk.E)
        self.open_lots_tree.column('avg_price', width=110, anchor=tk.E)
        self.open_lots_tree.column('avg_price_with_returns', width=140, anchor=tk.E) # คอลัมน์ใหม่
        self.open_lots_tree.column('total_returns', width=120, anchor=tk.E)

        self.open_lots_tree.tag_configure('parent_row', font=('Helvetica', 14 )) # Added for consistency
        self.open_lots_tree.tag_configure('grand_total', font=('Helvetica', 14, 'bold'), background="#CFCD96", foreground='blue') # Changed background to match closed_trades_tree
        self.open_lots_tree.tag_configure('child_row', foreground='gray50') # Optional: style for child rows

        # --- สร้าง Scrollbars ---
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.open_lots_tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.open_lots_tree.xview)
        self.open_lots_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # --- จัดวาง Treeview และ Scrollbars ---
        self.open_lots_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # --- โหลดข้อมูล ---
        self.load_open_lots_data()

    def create_tab2_widgets(self):
        """สร้างวิดเจ็ตสำหรับแท็บที่ 2 (หุ้นที่ขายไปแล้ว)"""
        container = ttk.Frame(self.tab2)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # --- สร้าง Treeview สำหรับแสดงข้อมูล ---
        columns = ('symbol', 'date_info', 'volume', 'avg_cost_price', 'avg_sell_price', 'total_cost', 'total_sale', 'sale_pl', 'dividends', 'total_pl')
        self.closed_trades_tree = ttk.Treeview(container, columns=columns, show='tree headings', style="Yellow.Treeview")

        # --- กำหนด Header และความกว้างของคอลัมน์ ---
        self.closed_trades_tree.heading('#0', text='')
        self.closed_trades_tree.column('#0', width=25, stretch=tk.NO)

        self.closed_trades_tree.heading('symbol', text='ชื่อหุ้น / Lot')
        self.closed_trades_tree.heading('date_info', text='วันที่ขาย')
        self.closed_trades_tree.heading('volume', text='จำนวนหุ้น')
        self.closed_trades_tree.heading('avg_cost_price', text='ต้นทุน/หุ้น')
        self.closed_trades_tree.heading('avg_sell_price', text='ราคาขาย/หุ้น')
        self.closed_trades_tree.heading('total_cost', text='เงินต้นทุน')
        self.closed_trades_tree.heading('total_sale', text='เงินที่ได้จากการขาย')
        self.closed_trades_tree.heading('sale_pl', text='กำไร/ขาดทุนจากการขาย')
        self.closed_trades_tree.heading('dividends', text='ปันผล+เงินคืน')
        self.closed_trades_tree.heading('total_pl', text='กำไรรวม')

        for col in columns:
            self.closed_trades_tree.column(col, width=110, anchor=tk.E)
        self.closed_trades_tree.column('symbol', width=150, anchor=tk.W)
        self.closed_trades_tree.column('date_info', anchor=tk.CENTER)

        # --- สร้าง Tags สำหรับ Style ---
        self.closed_trades_tree.tag_configure('parent_row', font=('Helvetica', 14))
        self.closed_trades_tree.tag_configure('child_row', foreground='gray50')
        self.closed_trades_tree.tag_configure('grand_total', font=('Helvetica', 14, 'bold'), background="#CFCD96", foreground='blue')
        self.closed_trades_tree.tag_configure('profit', foreground='#000000')  # กำไรเป็นสีดำ   
        self.closed_trades_tree.tag_configure('loss', foreground='red')

        # --- สร้าง Scrollbars ---
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.closed_trades_tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.closed_trades_tree.xview)
        self.closed_trades_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # --- จัดวาง ---
        self.closed_trades_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # --- โหลดข้อมูล ---
        self.load_closed_trades_data()

    def create_tab3_widgets(self):
        """สร้างวิดเจ็ตสำหรับแท็บที่ 3 (เงินปันผลและเงินคืน)"""
        container = ttk.Frame(self.tab3)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # --- สร้าง Treeview ---
        columns = ('symbol', 'lot_number', 'date', 'dividend_amount', 'return_amount', 'total_received')
        self.returns_tree = ttk.Treeview(container, columns=columns, show='tree headings', style="Orange.Treeview")

        # --- กำหนด Header และความกว้าง ---
        self.returns_tree.heading('#0', text='')
        self.returns_tree.column('#0', width=25, stretch=tk.NO)

        self.returns_tree.heading('symbol', text='ชื่อหุ้น')
        self.returns_tree.heading('lot_number', text='Lot Number')
        self.returns_tree.heading('date', text='วันที่ได้รับเงิน')
        self.returns_tree.heading('dividend_amount', text='เงินปันผล')
        self.returns_tree.heading('return_amount', text='เงินคืนทุน')
        self.returns_tree.heading('total_received', text='รวมที่ได้รับ')

        for col in columns:
            self.returns_tree.column(col, width=150, anchor=tk.E)
        self.returns_tree.column('total_received', width=160, anchor=tk.E)
        self.returns_tree.column('symbol', anchor=tk.W)
        self.returns_tree.column('lot_number', anchor=tk.W)
        self.returns_tree.column('date', anchor=tk.CENTER)

        # --- สร้าง Tags ---
        self.returns_tree.tag_configure('grand_total', font=('Helvetica', 14, 'bold'), background="#CFCD96", foreground='blue')

        # --- สร้าง Scrollbars ---
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.returns_tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.returns_tree.xview)
        self.returns_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.returns_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.load_returns_data()

    def _get_profit_tags(self, value):
        """คืนค่า tag 'profit' หรือ 'loss' ตามค่าของตัวเลข"""
        if value is None:
            return ()
        try:
            if float(value) > 0:
                return ('profit',)
            elif float(value) < 0:
                return ('loss',)
        except (ValueError, TypeError):
            return ()
        return ()
        
    def _get_thai_month_name(self, month_year_key):
        """Converts 'YYYY-MM' to 'เดือนย่อ YYYY' (Thai month name)"""
        year, month = map(int, month_year_key.split('-'))
        thai_months = [
            "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
            "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
        ]
        # ปี พ.ศ. (เพิ่ม 543)
        thai_year = year + 543 
        return f"{thai_months[month-1]} {thai_year}"

    def _format_number(self, value, is_float=True):
        """จัดรูปแบบตัวเลขให้มี comma และทศนิยม 2 ตำแหน่งสำหรับ float"""
        if value is None:
            return ""
        if is_float:
            return f"{value:,.2f}"
        else:
            return f"{value:,}"

    def load_open_lots_data(self):
        """โหลดข้อมูลหุ้นที่ถือครอง, จัดกลุ่มตามชื่อหุ้น, และแสดงผลใน Treeview"""
        for item in self.open_lots_tree.get_children():
            self.open_lots_tree.delete(item)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        l.lot_id, l.symbol, l.lot_number, l.buy_date, 
                        l.buy_volume, l.buy_price_per_unit, l.buy_commission, 
                        l.remaining_volume,
                        COALESCE(r.total_return, 0) AS total_return
                    FROM lots l
                    LEFT JOIN ( -- แก้ไข: เปลี่ยนการ JOIN จาก lot_id เป็น lot_number
                        SELECT lot_number, SUM(net_amount) as total_return
                        FROM (
                            SELECT lot_id as lot_number, (amount - COALESCE(tax, 0)) as net_amount FROM dividends -- หักภาษีออกจากปันผล
                            UNION ALL 
                            SELECT lot_id as lot_number, amount as net_amount FROM capital_returns
                        )
                        GROUP BY lot_number
                    ) r ON l.lot_number = r.lot_number -- แก้ไข: เปลี่ยนเงื่อนไขการ JOIN เป็น lot_number
                    WHERE l.status = 'OPEN' AND l.remaining_volume > 0
                    ORDER BY l.symbol, l.buy_date;
                """)
                all_open_lots = cursor.fetchall()

                grouped_lots = defaultdict(list)
                for lot in all_open_lots:
                    grouped_lots[lot['symbol']].append(lot)

                grand_total_invested = 0
                grand_total_cost = 0
                grand_total_returns = 0

                for symbol, lots_list in grouped_lots.items():
                    total_volume = sum(lot['remaining_volume'] for lot in lots_list)
                    total_invested_amount = sum((lot['buy_volume'] * lot['buy_price_per_unit']) + (lot['buy_commission'] or 0) for lot in lots_list)
                    total_cost_basis = sum(
                        (lot['remaining_volume'] / lot['buy_volume']) * ((lot['buy_volume'] * lot['buy_price_per_unit']) + (lot['buy_commission'] or 0))
                        for lot in lots_list if lot['buy_volume'] > 0
                    )
                    avg_price = total_cost_basis / total_volume if total_volume > 0 else 0
                    total_returns_for_symbol = sum(lot['total_return'] for lot in lots_list)
                    # คำนวณราคาเฉลี่ยหลังหักปันผล
                    avg_price_with_returns = (total_cost_basis - total_returns_for_symbol) / total_volume if total_volume > 0 else 0

                    parent_values = (
                        symbol,
                        self._format_number(len(lots_list), is_float=False),
                        self._format_number(total_volume, is_float=False),
                        self._format_number(total_invested_amount),
                        self._format_number(total_cost_basis),
                        self._format_number(avg_price),
                        self._format_number(avg_price_with_returns), # เพิ่มค่าสำหรับคอลัมน์ใหม่
                        self._format_number(total_returns_for_symbol),
                    )
                    parent_iid = self.open_lots_tree.insert('', tk.END, values=parent_values, open=False, tags=('parent_row',))

                    grand_total_invested += total_invested_amount
                    grand_total_cost += total_cost_basis
                    grand_total_returns += total_returns_for_symbol

                    for lot in lots_list:
                        invested_amount_for_lot = (lot['buy_volume'] * lot['buy_price_per_unit']) + (lot['buy_commission'] or 0)
                        cost_basis_for_lot = (lot['remaining_volume'] / lot['buy_volume']) * invested_amount_for_lot if lot['buy_volume'] > 0 else 0
                        # สำหรับแถวย่อย หัวคอลัมน์คือ "ราคาซื้อ/หน่วย" และ "เฉลี่ยรวมปันผล/หุ้น"
                        # เราจะแสดงราคาซื้อ และเว้นว่างในช่องเฉลี่ยรวมปันผล

                        child_values = (
                            f"  └ {lot['lot_number']}",
                            lot['buy_date'],
                            self._format_number(lot['buy_volume'], is_float=False),
                            self._format_number(invested_amount_for_lot),
                            f"{self._format_number(lot['remaining_volume'], is_float=False)} ({self._format_number(cost_basis_for_lot)})",
                            self._format_number(lot['buy_price_per_unit']), # ราคาซื้อ/หน่วย
                            "", # เว้นว่างสำหรับคอลัมน์ใหม่ในแถวย่อย
                            self._format_number(lot['total_return'])
                        )
                        self.open_lots_tree.insert(parent_iid, tk.END, values=child_values, tags=('child_row',))

                if all_open_lots:
                    self.open_lots_tree.insert('', tk.END, values=(), tags=('grand_total',)) # Spacer
                    grand_total_values = (
                        'ผลรวมทั้งหมด', '', '',
                        self._format_number(grand_total_invested),
                        self._format_number(grand_total_cost),
                        '', '', # avg_price, avg_price_with_returns
                        self._format_number(grand_total_returns)
                    )
                    self.open_lots_tree.insert('', tk.END, values=grand_total_values, tags=('grand_total',))

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถโหลดข้อมูลหุ้นที่ถือครองได้: {e}", parent=self)

    def load_closed_trades_data(self):
        """
        แก้ไขใหม่: โหลดข้อมูล 'รายการขาย' (Sale Transactions) ทั้งหมดเพื่อแสดง Realized P/L
        โดยดึงข้อมูลจากตาราง sales เป็นหลัก แล้ว join กับ lots เพื่อหาต้นทุน
        """
        for item in self.closed_trades_tree.get_children():
            self.closed_trades_tree.delete(item)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        s.sale_id,
                        s.sell_date,
                        s.sell_volume,
                        s.sell_price_per_unit,
                        s.sell_commission,
                        l.symbol,
                        l.lot_number,
                        l.buy_volume,
                        l.buy_price_per_unit,
                        l.buy_commission,
                        COALESCE(r.total_return, 0) AS total_dividends_returns -- เพิ่มการดึงข้อมูลปันผล
                    FROM sales s
                    JOIN lots l ON s.lot_id = l.lot_number -- ใช้ lot_number ในการ Join
                    -- เพิ่มการ Join เพื่อดึงข้อมูลปันผลและเงินคืนทุน
                    LEFT JOIN (
                        SELECT lot_number, SUM(net_amount) as total_return
                        FROM (
                            SELECT lot_id as lot_number, (amount - COALESCE(tax, 0)) as net_amount FROM dividends -- หักภาษีออกจากปันผล
                            UNION ALL
                            SELECT lot_id as lot_number, amount as net_amount FROM capital_returns
                        )
                        GROUP BY lot_number
                    ) r ON l.lot_number = r.lot_number
                    ORDER BY l.symbol, s.sell_date DESC;
                """)
                all_sales = cursor.fetchall()

                # จัดกลุ่มข้อมูลตามชื่อหุ้น
                grouped_sales = defaultdict(list)
                for sale in all_sales:
                    grouped_sales[sale['symbol']].append(sale)

                grand_total_cost = 0
                grand_total_sale = 0
                grand_total_sale_pl = 0
                grand_total_dividends = 0 # เพิ่มตัวแปรสำหรับรวมยอดปันผล
                grand_total_pl = 0 # เพิ่มตัวแปรสำหรับรวมกำไรทั้งหมด

                for symbol, sales_list in grouped_sales.items():
                    # ตัวแปรสำหรับรวมยอดของแต่ละหุ้น (Symbol Total)
                    sym_total_volume = 0
                    sym_total_cost = 0
                    sym_total_sale = 0
                    sym_total_sale_pl = 0
                    sym_total_dividends = 0
                    sym_total_pl = 0

                    # รอบแรก: คำนวณยอดรวมของหุ้นตัวนี้
                    for sale in sales_list:
                        original_lot_cost = (sale['buy_volume'] * sale['buy_price_per_unit']) + (sale['buy_commission'] or 0)
                        cost_for_this_sale = (sale['sell_volume'] / sale['buy_volume']) * original_lot_cost if sale['buy_volume'] > 0 else 0
                        sale_value_net = (sale['sell_volume'] * sale['sell_price_per_unit']) - (sale['sell_commission'] or 0)
                        dividends_for_this_sale = sale['total_dividends_returns']
                        sale_pl = sale_value_net - cost_for_this_sale
                        total_pl = sale_pl + dividends_for_this_sale

                        sym_total_volume += sale['sell_volume']
                        sym_total_cost += cost_for_this_sale
                        sym_total_sale += sale_value_net
                        sym_total_sale_pl += sale_pl
                        sym_total_dividends += dividends_for_this_sale
                        sym_total_pl += total_pl

                    # คำนวณค่าเฉลี่ย
                    sym_avg_cost = sym_total_cost / sym_total_volume if sym_total_volume > 0 else 0
                    sym_avg_sell = sym_total_sale / sym_total_volume if sym_total_volume > 0 else 0

                    # เพิ่มแถว Parent (ชื่อหุ้นและยอดรวม)
                    parent_values = (
                        symbol,
                        f"{len(sales_list)} รายการ",
                        self._format_number(sym_total_volume, is_float=False),
                        self._format_number(sym_avg_cost),
                        self._format_number(sym_avg_sell),
                        self._format_number(sym_total_cost),
                        self._format_number(sym_total_sale),
                        self._format_number(sym_total_sale_pl),
                        self._format_number(sym_total_dividends),
                        self._format_number(sym_total_pl)
                    )
                    parent_tags = ('parent_row',) + self._get_profit_tags(sym_total_pl)
                    parent_iid = self.closed_trades_tree.insert('', tk.END, values=parent_values, open=False, tags=parent_tags)

                    # สะสมยอด Grand Total
                    grand_total_cost += sym_total_cost
                    grand_total_sale += sym_total_sale
                    grand_total_sale_pl += sym_total_sale_pl
                    grand_total_dividends += sym_total_dividends
                    grand_total_pl += sym_total_pl

                    # รอบสอง: เพิ่มแถว Child (รายละเอียดแต่ละรายการขาย)
                    for sale in sales_list:
                        original_lot_cost = (sale['buy_volume'] * sale['buy_price_per_unit']) + (sale['buy_commission'] or 0)
                        cost_for_this_sale = (sale['sell_volume'] / sale['buy_volume']) * original_lot_cost if sale['buy_volume'] > 0 else 0
                        cost_per_share = original_lot_cost / sale['buy_volume'] if sale['buy_volume'] > 0 else 0
                        sale_value_net = (sale['sell_volume'] * sale['sell_price_per_unit']) - (sale['sell_commission'] or 0)
                        dividends_for_this_sale = sale['total_dividends_returns']
                        sale_pl = sale_value_net - cost_for_this_sale
                        total_pl = sale_pl + dividends_for_this_sale

                        child_values = (
                            f"  └ {sale['lot_number']}",
                            sale['sell_date'],
                            self._format_number(sale['sell_volume'], is_float=False),
                            self._format_number(cost_per_share),
                            self._format_number(sale['sell_price_per_unit']),
                            self._format_number(cost_for_this_sale),
                            self._format_number(sale_value_net),
                            self._format_number(sale_pl),
                            self._format_number(dividends_for_this_sale),
                            self._format_number(total_pl)
                        )
                        child_tags = ('child_row',) + self._get_profit_tags(total_pl)
                        self.closed_trades_tree.insert(parent_iid, tk.END, values=child_values, tags=child_tags)

                # --- แสดงแถวสรุปรวม (Grand Total) ---
                if all_sales:
                    self.closed_trades_tree.insert('', tk.END, values=(), tags=('grand_total',))

                    grand_total_values = (
                        'ผลรวมทั้งหมด', '', '', '', '',
                        self._format_number(grand_total_cost),
                        self._format_number(grand_total_sale),
                        self._format_number(grand_total_sale_pl),
                        self._format_number(grand_total_dividends), # แสดงปันผลรวม
                        self._format_number(grand_total_pl) # แสดงกำไรรวมทั้งหมด
                    )
                    tags = ('grand_total',) + self._get_profit_tags(grand_total_pl)
                    self.closed_trades_tree.insert('', tk.END, values=grand_total_values, tags=tags)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถโหลดข้อมูลหุ้นที่ขายไปแล้วได้: {e}", parent=self)

    def load_returns_data(self):
        """โหลดข้อมูลเงินปันผลและเงินคืนทุนทั้งหมด และแสดงในแท็บที่ 3"""
        for item in self.returns_tree.get_children():
            self.returns_tree.delete(item)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        l.symbol,
                        l.lot_number,
                        r.payment_date,
                        r.amount,
                        r.type
                    FROM (
                        SELECT lot_id, payment_date, (amount - COALESCE(tax, 0)) as amount, 'dividend' as type FROM dividends -- หักภาษี
                        UNION ALL
                        SELECT lot_id, payment_date, amount, 'return' as type FROM capital_returns
                    ) r
                    JOIN lots l ON r.lot_id = l.lot_number -- แก้ไข Join เป็น lot_number ให้ตรงกับข้อมูลที่เก็บ
                    ORDER BY l.symbol, l.lot_number, r.payment_date;
                """)
                all_returns = cursor.fetchall()
                grand_total_dividends = 0
                grand_total_returns = 0

                # --- จัดกลุ่มข้อมูลเป็น Tree ---
                grouped_by_symbol = defaultdict(list)
                for row in all_returns:
                    grouped_by_symbol[row['symbol']].append(row)

                for symbol, records in grouped_by_symbol.items():
                    # คำนวณยอดรวมของ Symbol
                    symbol_dividends = sum(r['amount'] for r in records if r['type'] == 'dividend')
                    symbol_returns = sum(r['amount'] for r in records if r['type'] == 'return')
                    symbol_total = symbol_dividends + symbol_returns

                    # สร้างแถวหลักสำหรับ Symbol
                    symbol_parent_iid = self.returns_tree.insert('', tk.END, open=False, values=(
                        symbol,
                        f"{len(records)} รายการ",
                        "",
                        self._format_number(symbol_dividends),
                        self._format_number(symbol_returns),
                        self._format_number(symbol_total)
                    ))

                    # จัดกลุ่มย่อยตาม Lot Number
                    grouped_by_lot = defaultdict(list)
                    for record in records:
                        grouped_by_lot[record['lot_number']].append(record)

                    for lot_number, lot_records in grouped_by_lot.items():
                        # แทรกข้อมูลของแต่ละรายการภายใต้ Symbol
                        for record in lot_records:
                            dividend_amount = record['amount'] if record['type'] == 'dividend' else 0
                            return_amount = record['amount'] if record['type'] == 'return' else 0

                            child_values = (
                                f"  └ {record['symbol']}",
                                record['lot_number'],
                                record['payment_date'],
                                self._format_number(dividend_amount) if dividend_amount else "",
                                self._format_number(return_amount) if return_amount else "",
                                self._format_number(record['amount']) # ยอดรวมของรายการนั้นๆ
                            )
                            self.returns_tree.insert(symbol_parent_iid, tk.END, values=child_values)

                # คำนวณ Grand Total จากข้อมูลทั้งหมด
                grand_total_dividends = sum(r['amount'] for r in all_returns if r['type'] == 'dividend')
                grand_total_returns = sum(r['amount'] for r in all_returns if r['type'] == 'return')

                # --- สรุปรวมท้ายตาราง ---
                if all_returns:
                    self.returns_tree.insert('', tk.END, values=(), tags=('grand_total',)) # Spacer

                    grand_total_parent_iid = self.returns_tree.insert('', tk.END, values=(), open=False, tags=('grand_total',))
                    grand_total_all = grand_total_dividends + grand_total_returns
                    grand_total_values = (
                        'ผลรวมทั้งหมด', '', '', # symbol, lot_number, date
                        self._format_number(grand_total_dividends),
                        self._format_number(grand_total_returns),
                        self._format_number(grand_total_all)
                    )
                    self.returns_tree.item(grand_total_parent_iid, values=grand_total_values)

                    # จัดกลุ่มตามเดือน
                    monthly_summary = defaultdict(lambda: {'dividends': 0, 'returns': 0})
                    for row in all_returns:
                        month_key = datetime.strptime(row['payment_date'], '%Y-%m-%d').strftime('%Y-%m')
                        if row['type'] == 'dividend':
                            monthly_summary[month_key]['dividends'] += row['amount']
                        else:
                            monthly_summary[month_key]['returns'] += row['amount']

                    # แทรกสรุปรายเดือน
                    for month_key in sorted(monthly_summary.keys()):
                        summary = monthly_summary[month_key]
                        month_name = self._get_thai_month_name(month_key)
                        monthly_total = summary['dividends'] + summary['returns']
                        monthly_values = (
                            f"  └ {month_name}", '', '', # symbol, lot_number, date
                            self._format_number(summary['dividends']),
                            self._format_number(summary['returns']),
                            self._format_number(monthly_total)
                        )
                        self.returns_tree.insert(grand_total_parent_iid, tk.END, values=monthly_values)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถโหลดข้อมูลเงินปันผล/คืนทุนได้: {e}", parent=self)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        app = StockAnalyzeApp(db_path)
        app.mainloop()
    else:
        print("Please provide the database path as a command-line argument.")



  
