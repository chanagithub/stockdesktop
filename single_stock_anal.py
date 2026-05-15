import tkinter as tk
from tkinter import ttk, messagebox
import chmodule as cm
from collections import defaultdict
import sqlite3
import sys
import os
from datetime import datetime
# --- เพิ่มการนำเข้าไลบรารีสำหรับจัดการรูปภาพ ---
try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Library Missing", "ไม่ได้ติดตั้งไลบรารี Pillow\nกรุณาติดตั้งด้วยคำสั่ง: pip install Pillow")
    Image = None
    ImageTk = None
from tkcalendar import DateEntry # นำเข้าโดยตรง

class Single_Stock_Analyzer_app(tk.Toplevel): # <-- 1. เปลี่ยนเป็น Toplevel
    def __init__(self, parent, db_path, door_icon):
        super().__init__(parent) # <-- 2. ส่ง parent ไปให้ super class
        self.parent = parent
        self.db_path = db_path
        self.title("Stock Analyzer")
        self.attributes("-topmost", True)

        # ขยายหน้าต่างเพื่อรองรับตาราง
        cm.ChClass.setwindowcenter(self, 1100, 600)
        self.background_color = "#214936"
        self.configure(bg=self.background_color)
        self.lots_data = [] # เก็บข้อมูลล็อตที่โหลดมา
        self.door_icon = door_icon # <-- 3. รับไอคอนมาโดยตรง
        self.create_widgets()   
        self.load_open_stock_symbols()

    def create_widgets(self):
        # --- Frame สำหรับส่วนกรอกข้อมูล ---
        top_frame = tk.Frame(self, bg=self.background_color)
        top_frame.pack(pady=10, padx=10, fill='x')
        # --- เพิ่ม: ทำให้คอลัมน์ที่ 2 ขยายตัวเพื่อดันไอคอนไปทางขวา ---
        top_frame.columnconfigure(2, weight=1)

        # --- แถวที่ 0: เลือกหุ้น ---
        tk.Label(top_frame, text="เลือกหุ้น:", bg=self.background_color, fg="white").grid(row=0, column=0, padx=(0, 5), pady=5, sticky='w')
        self.symbol_combo = ttk.Combobox(top_frame, state="readonly", width=15)
        self.symbol_combo.grid(row=0, column=1, pady=5, sticky='w')
        self.symbol_combo.bind("<<ComboboxSelected>>", self.load_lots_for_symbol)

        # --- แถวที่ 1: ราคาปัจจุบัน ---
        tk.Label(top_frame, text="ราคาหุ้นปัจจุบัน:", bg=self.background_color, fg="white").grid(row=1, column=0, padx=(0, 5), pady=5, sticky='w')
        self.current_price_entry = tk.Entry(top_frame, width=16) # กำหนดความกว้างให้ใกล้เคียงกับ Combobox
        self.current_price_entry.grid(row=1, column=1, pady=5, sticky='w')
        self.current_price_entry.bind("<KeyRelease>", self.calculate_unrealized_pl)

        # --- สร้าง Canvas สำหรับปุ่มขอบมน ---
        # ไม่จำเป็นต้องมีปุ่ม Analyze แยกแล้ว เพราะจะคำนวณอัตโนมัติ

        # --- เพิ่มรูปประตูสำหรับปิดโปรแกรม ---
        if self.door_icon:
            exit_label = tk.Label(top_frame, image=self.door_icon, bg=self.background_color, cursor="hand2")
            exit_label.grid(row=0, column=3, rowspan=2, padx=(20, 0), sticky='e') # ย้ายไป column 3 และจัดชิดขวา
            exit_label.bind("<Button-1>", lambda event: self.destroy())
            cm.ChClass.CreateToolTip(exit_label, "ปิดหน้าต่างนี้")

        # --- Frame สำหรับตารางและ Checkbox ---
        result_frame = tk.Frame(self, bg=self.background_color)
        result_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(1, weight=1)

        # --- Checkbox "เลือกล็อตทั้งหมด" ---
        self.select_all_var = tk.BooleanVar()
        select_all_check = tk.Checkbutton(
            result_frame, text="เลือกล็อตทั้งหมด", variable=self.select_all_var,
            bg=self.background_color, fg="white", selectcolor=self.background_color,
            command=self.toggle_select_all
        )
        select_all_check.grid(row=0, column=0, sticky='w')

        # --- สร้าง Treeview สำหรับแสดงผล ---
        columns = ('select', 'buy_date', 'lot_number', 'buy_price', 'volume', 'cost', 'dividends', 'sale_value', 'pl', 'total_pl')
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings')

        # --- กำหนด Header ---
        self.tree.heading('select', text='เลือก')
        self.tree.heading('buy_date', text='วันที่ซื้อ')
        self.tree.heading('lot_number', text='Lot Number')
        self.tree.heading('buy_price', text='ราคาซื้อ/หุ้น')
        self.tree.heading('volume', text='หุ้นคงเหลือ')
        self.tree.heading('cost', text='ต้นทุนรวม')
        self.tree.heading('dividends', text='เงินปันผลรวม')
        self.tree.heading('sale_value', text='มูลค่าปัจจุบัน')
        self.tree.heading('pl', text='กำไร/ขาดทุน')
        self.tree.heading('total_pl', text='กำไรรวม (รวมปันผล)')

        # --- กำหนดความกว้างและจัดวางคอลัมน์ ---
        self.tree.column('select', width=50, anchor=tk.CENTER, stretch=False)
        self.tree.column('buy_date', width=100, anchor=tk.CENTER)
        self.tree.column('lot_number', width=150, anchor=tk.W)
        self.tree.column('buy_price', width=100, anchor=tk.E)
        self.tree.column('volume', width=100, anchor=tk.E)
        self.tree.column('dividends', width=120, anchor=tk.E)
        self.tree.column('cost', width=120, anchor=tk.E)
        self.tree.column('sale_value', width=120, anchor=tk.E)
        self.tree.column('pl', width=120, anchor=tk.E)
        self.tree.column('total_pl', width=150, anchor=tk.E)

        # --- สร้าง Scrollbar ---
        vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        # --- จัดวาง Treeview และ Scrollbar ---
        self.tree.grid(row=1, column=0, sticky='nsew')
        vsb.grid(row=1, column=1, sticky='ns')

        # --- กำหนด Tags สำหรับสี ---
        self.tree.tag_configure('profit', foreground='green')
        self.tree.tag_configure('loss', foreground='red')
        self.tree.tag_configure('total', font=('Helvetica', 14, 'bold'), background='lightgrey',foreground='black')

        # --- ผูก Event การคลิกบน Treeview ---
        self.tree.bind('<Button-1>', self.on_tree_click)

    def on_tree_click(self, event):
        """จัดการการคลิกบน Treeview เพื่อสลับสถานะ Checkbox"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column_id = self.tree.identify_column(event.x)
        if self.tree.column(column_id, "id") != "select":
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # สลับสถานะ 'checked'
        tags = list(self.tree.item(item_id, "tags"))
        if "checked" in tags:
            tags.remove("checked")
            self.tree.set(item_id, 'select', '☐')
        else:
            tags.append("checked")
            self.tree.set(item_id, 'select', '☑')
        self.tree.item(item_id, tags=tags)

        self.calculate_unrealized_pl() # คำนวณใหม่เมื่อมีการเปลี่ยนแปลง

    def load_open_stock_symbols(self):
        """ดึงรายชื่อหุ้นที่ยังถือครอง (status='OPEN') จากฐานข้อมูล"""
        if not self.db_path or not os.path.exists(self.db_path):
            self.symbol_combo['values'] = ["ไม่พบ DB"]
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT symbol 
                    FROM lots 
                    WHERE status = 'OPEN' AND remaining_volume > 0 
                    ORDER BY symbol
                """)
                symbols = [row[0] for row in cursor.fetchall()]
                if symbols:
                    self.symbol_combo['values'] = symbols
                else:
                    self.symbol_combo['values'] = ["ไม่มีหุ้น"]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถโหลดรายชื่อหุ้นได้: {e}", parent=self)
            self.symbol_combo['values'] = ["Error"]

    def load_lots_for_symbol(self, event=None):
        """เมื่อเลือกหุ้น ให้โหลดข้อมูลล็อตทั้งหมดมาแสดงในตาราง"""
        symbol = self.symbol_combo.get()
        if not symbol or symbol in ["ไม่มีหุ้น", "Error"]:
            return

        # ล้างข้อมูลเก่า
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.lots_data.clear()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # ดึงข้อมูลล็อตพร้อมกับเงินปันผล/คืนทุน
                cursor.execute("""
                    SELECT
                        l.symbol, l.lot_id, l.lot_number, l.buy_date, l.buy_price_per_unit, l.remaining_volume,
                        (l.buy_volume * l.buy_price_per_unit) + COALESCE(l.buy_commission, 0) AS original_cost,
                        l.buy_volume,
                        COALESCE(r.total_return, 0) AS total_return
                    FROM lots l
                    LEFT JOIN (
                        SELECT lot_id, SUM(amount) as total_return
                        FROM (
                            SELECT lot_id, (amount - COALESCE(tax, 0)) as amount FROM dividends
                            UNION ALL
                            SELECT lot_id, amount FROM capital_returns
                        ) GROUP BY lot_id
                    ) r ON l.lot_number = r.lot_id
                    WHERE l.symbol = ? AND l.status = 'OPEN' AND l.remaining_volume > 0
                    ORDER BY l.buy_date
                """, (symbol,))
                self.lots_data = cursor.fetchall()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถโหลดข้อมูลล็อตได้: {e}", parent=self)
            return

        # แสดงข้อมูลใน Treeview
        for lot in self.lots_data:
            cost_basis = (lot['remaining_volume'] / lot['buy_volume']) * lot['original_cost'] if lot['buy_volume'] > 0 else 0
            self.tree.insert('', 'end', iid=lot['lot_id'], values=(
                '☐', # Checkbox
                lot['buy_date'],
                lot['lot_number'],
                f"{lot['buy_price_per_unit']:,.2f}",
                f"{lot['remaining_volume']:,}",
                f"{cost_basis:,.2f}",
                f"{lot['total_return']:,.2f}", "", "", ""
            ))
        self.select_all_var.set(False)
        self.calculate_unrealized_pl()

    def toggle_select_all(self):
        """เลือกหรือยกเลิกการเลือกทั้งหมด"""
        is_selected = self.select_all_var.get()
        checkbox_char = '☑' if is_selected else '☐'

        for item_id in self.tree.get_children():
            if "total_row" in self.tree.item(item_id, "tags"): continue # ข้ามแถวสรุป
            tags = list(self.tree.item(item_id, "tags"))
            if is_selected:
                if "checked" not in tags:
                    tags.append("checked")
            else:
                if "checked" in tags:
                    tags.remove("checked")
            self.tree.item(item_id, tags=tags)
            self.tree.set(item_id, 'select', checkbox_char)
        self.calculate_unrealized_pl()

    def calculate_unrealized_pl(self, event=None):
        """คำนวณกำไร/ขาดทุนที่ยังไม่เกิดขึ้นจริงตามราคาปัจจุบันและล็อตที่เลือก"""
        try:
            current_price = float(self.current_price_entry.get() or 0)
        except ValueError:
            current_price = 0

        # ลบแถวสรุปเก่าออกก่อน
        if self.tree.exists("total_row"):
            self.tree.delete("total_row")

        total_cost = 0
        total_sale_value = 0
        total_pl = 0
        total_pl_with_returns = 0
        total_dividends = 0 # เพิ่มตัวแปรสำหรับรวมเงินปันผล

        # แก้ไข: แปลง item ID (string) ให้เป็น integer เพื่อให้เปรียบเทียบกับ lot_id (integer) ได้ถูกต้อง
        selected_ids = {int(item) for item in self.tree.get_children() if "checked" in self.tree.item(item, "tags")}

        for lot in self.lots_data:
            lot_id = lot['lot_id']
            cost_basis = (lot['remaining_volume'] / lot['buy_volume']) * lot['original_cost'] if lot['buy_volume'] > 0 else 0
            sale_value = lot['remaining_volume'] * current_price
            pl = sale_value - cost_basis
            total_pl_lot = pl + lot['total_return']

            if lot_id in selected_ids:
                total_dividends += lot['total_return']
                total_cost += cost_basis
                total_sale_value += sale_value
                total_pl += pl
                total_pl_with_returns += total_pl_lot

            # อัปเดตข้อมูลในแถว
            current_tags = list(self.tree.item(lot_id, "tags"))
            pl_tags = ('loss',) if pl < 0 else ('profit',)
            # แก้ไข: รวม tag ที่มีอยู่เดิม (เช่น 'checked') กับ tag สี
            final_tags = [t for t in current_tags if t not in ['profit', 'loss']] + list(pl_tags)

            self.tree.set(lot_id, 'sale_value', f"{sale_value:,.2f}")
            self.tree.set(lot_id, 'pl', f"{pl:,.2f}")
            self.tree.set(lot_id, 'total_pl', f"{total_pl_lot:,.2f}")
            self.tree.item(lot_id, tags=final_tags) # อัปเดต tags ทั้งหมด

        # เพิ่มแถวสรุปผลรวม
        if selected_ids:
            pl_tags = ('loss',) if total_pl < 0 else ('profit',)
            total_pl_tags = ('loss',) if total_pl_with_returns < 0 else ('profit',)

            # แก้ไขล่าสุด: แก้ไขการจัดเรียงค่า values ให้ตรงกับจำนวนคอลัมน์ที่ถูกต้อง
            self.tree.insert('', 'end', iid="total_row", values=(
                '', 'ผลรวม', '', '', '', # select, buy_date, lot_number, buy_price, volume
                f"{total_cost:,.2f}", f"{total_dividends:,.2f}", f"{total_sale_value:,.2f}", f"{total_pl:,.2f}", f"{total_pl_with_returns:,.2f}"
            ), tags=('total',))
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        if os.path.exists(db_path):
            app = Single_Stock_Analyzer_app(db_path)
            app.mainloop()
        else:
            # สร้างหน้าต่างชั่วคราวเพื่อแสดงข้อความ
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("เกิดข้อผิดพลาด", f"ไม่พบไฟล์ฐานข้อมูลที่:\n{db_path}")
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("เกิดข้อผิดพลาด", "ไม่ได้ระบุไฟล์ฐานข้อมูล\nกรุณาเปิดโปรแกรมนี้ผ่านหน้าต่างหลัก")
 