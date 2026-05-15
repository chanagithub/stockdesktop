import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import sqlite3
import chmodule

class StockLogApp(tk.Toplevel):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db_path = db_path

        if not os.path.exists(self.db_path):
            messagebox.showerror("เกิดข้อผิดพลาด", f"ไม่พบไฟล์ฐานข้อมูลที่:\n{db_path}")
            self.destroy()
            return

        self.title(f"ประวัติธุรกรรม - {os.path.basename(db_path)}")
        chmodule.ChClass.setwindowcenter(self, 1200, 700)
        self.attributes("-topmost", True)
        self.status_bar = chmodule.ChClass.status_bar("Ready", self)

        self.item_data = {} # สร้าง dictionary สำหรับเก็บข้อมูลเพิ่มเติมของแต่ละ item

        self.create_widgets()
        self.load_transaction_log()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(3, weight=1) # ให้คอลัมน์ที่ 3 ขยายเพื่อดันปุ่ม refresh ไปทางขวา

        # --- ส่วนกรองข้อมูล ---
        filter_label = ttk.Label(main_frame, text="ใส่ชื่อหุ้น:")
        filter_label.grid(row=0, column=0, sticky="w", padx=(0, 5))

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(main_frame, textvariable=self.search_var, width=20)
        search_entry.bind("<Return>", lambda event: self.load_transaction_log()) # กรองข้อมูลเมื่อกด Enter
        search_entry.grid(row=0, column=1, sticky="w", padx=(0, 5), pady=(0, 10))

        search_button = ttk.Button(main_frame, text="กรองข้อมูล", command=self.load_transaction_log)
        search_button.grid(row=0, column=2, sticky="w", pady=(0, 10))

        # --- ปุ่ม Refresh ---
        refresh_button = ttk.Button(main_frame, text="รีเฟรชข้อมูล", command=self.load_transaction_log)
        refresh_button.grid(row=0, column=4, sticky="e", pady=(0, 10))


        # --- Treeview สำหรับแสดงผล ---
        columns = ('date', 'type', 'symbol', 'description', 'amount', 'status', 'actions')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings')



        # --- กำหนด Header ---
        self.tree.heading('date', text='วันที่')
        self.tree.heading('type', text='ประเภท')
        self.tree.heading('symbol', text='ชื่อหุ้น')
        self.tree.heading('description', text='รายละเอียด')
        self.tree.heading('amount', text='จำนวนเงิน/หน่วย')
        self.tree.heading('status', text='สถานะ')
        self.tree.heading('actions', text='คำสั่ง')

        # --- กำหนดความกว้างและจัดวางคอลัมน์ ---
        self.tree.column('date', width=100, anchor=tk.CENTER)
        self.tree.column('type', width=100, anchor=tk.W)
        self.tree.column('symbol', width=100, anchor=tk.W)
        self.tree.column('description', width=400, anchor=tk.W)
        self.tree.column('amount', width=120, anchor=tk.E)
        self.tree.column('status', width=80, anchor=tk.CENTER)
        self.tree.column('actions', width=80, anchor=tk.CENTER)

        # --- สร้าง Scrollbar ---
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        # --- จัดวาง Treeview และ Scrollbar ---
        self.tree.grid(row=1, column=0, columnspan=5, sticky='nsew')
        vsb.grid(row=1, column=5, sticky='ns')

        # --- กำหนด Tags สำหรับสี ---
        self.tree.tag_configure('buy', foreground='green')
        self.tree.tag_configure('sell', foreground='red')
        self.tree.tag_configure('dividend', foreground='blue')
        self.tree.tag_configure('return', foreground='purple')
        self.tree.tag_configure('open', foreground='green')
        self.tree.tag_configure('closed', foreground='grey')

        # --- ผูก Event การคลิกบน Treeview ---
        self.tree.bind('<Button-1>', self.on_tree_click)
        # --- เพิ่ม: ผูก Event การเคลื่อนที่ของเมาส์ ---
        self.tree.bind('<Motion>', self.on_tree_motion)
        self.tree.bind('<Leave>', self.on_tree_leave)

    def load_transaction_log(self):
        # ล้างข้อมูลเก่า
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_data.clear() # ล้างข้อมูลใน dictionary ด้วย
        search_text = self.search_var.get().strip()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # ใช้ UNION ALL เพื่อรวมข้อมูลจากทุกตารางที่เกี่ยวข้อง
                query = """
                    SELECT 'Buy' as type, l.buy_date as date, l.symbol,
                           'ซื้อ ' || l.buy_volume || ' หุ้น @' || printf("%.2f", l.buy_price_per_unit) || ' (Lot: ' || l.lot_number || ')' as description,
                           (l.buy_volume * l.buy_price_per_unit) + COALESCE(l.buy_commission, 0) as amount,
                           'lots' as table_name, l.lot_id as record_id, l.status
                    FROM lots l

                    UNION ALL

                    SELECT 'Sell' as type, s.sell_date as date, l.symbol,
                           'ขาย ' || s.sell_volume || ' หุ้น @' || printf("%.2f", s.sell_price_per_unit) || ' (จาก Lot: ' || l.lot_number || ')' as description,
                           (s.sell_volume * s.sell_price_per_unit) - COALESCE(s.sell_commission, 0) as amount,
                           'sales' as table_name, s.sale_id as record_id, l.status
                    FROM sales s JOIN lots l ON s.lot_id = l.lot_number

                    UNION ALL

                    SELECT 'Dividend' as type, d.payment_date as date, l.symbol,
                           'ปันผลจาก Lot: ' || l.lot_number as description,
                           d.amount as amount,
                           'dividends' as table_name, d.id as record_id, l.status
                    FROM dividends d JOIN lots l ON d.lot_id = l.lot_number

                    UNION ALL

                    SELECT 'Capital Return' as type, cr.payment_date as date, l.symbol,
                           'คืนทุนจาก Lot: ' || l.lot_number as description,
                           cr.amount as amount,
                           'capital_returns' as table_name, cr.id as record_id, l.status
                    FROM capital_returns cr JOIN lots l ON cr.lot_id = l.lot_number

                    ORDER BY date DESC;
                """
                transactions = cursor.execute(query).fetchall()

                for i, trans in enumerate(transactions):
                    trans_type, date, symbol, desc, amount, table, rec_id, status = trans

                    # กรองข้อมูลตามชื่อหุ้น (symbol) ถ้ามี search_text
                    if search_text and search_text.lower() not in symbol.lower():
                        continue # ข้ามรายการนี้ถ้าไม่ตรงกับคำค้นหา
                    
                    type_tag = trans_type.lower().replace(' ', '')
                    status_tag = status.lower() if status else ''
                    
                    # สร้าง item id ที่ไม่ซ้ำกัน
                    item_id = f"item_{i}"

                    self.tree.insert('', 'end', iid=item_id, values=(
                        date, trans_type, symbol, desc, f"{amount:,.2f}", status, ""
                    ), tags=(type_tag, status_tag))

                    self.tree.item(item_id, values=(date, trans_type, symbol, desc, f"{amount:,.2f}", status, " ลบ "))
                    
                    # เก็บข้อมูล table และ record_id ไว้ใน dictionary โดยใช้ item_id เป็น key
                    self.item_data[item_id] = {'table': table, 'record_id': rec_id}

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"ไม่สามารถโหลดประวัติธุรกรรมได้: {e}", parent=self)

    def on_tree_motion(self, event):
        """จัดการเมื่อเมาส์เคลื่อนที่บน Treeview เพื่อแสดง Tooltip บน Status bar"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            self._update_statusbar("Ready")
            return

        column_id = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)

        if item_id and self.tree.column(column_id, "id") == "actions":
            self._update_statusbar("คลิกที่คำว่า ลบ เพื่อลบข้อมูล")
        else:
            self._update_statusbar("Ready")

    def on_tree_leave(self, event):
        """จัดการเมื่อเมาส์ออกจาก Treeview"""
        self._update_statusbar("Ready")

    def on_tree_click(self, event):
        """จัดการการคลิกบน Treeview เพื่อเรียกฟังก์ชันแก้ไขหรือลบ"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column_id = self.tree.identify_column(event.x)
        # ตรวจสอบว่าคลิกที่คอลัมน์ 'คำสั่ง' หรือไม่
        if self.tree.column(column_id, "id") != "actions":
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # ดึงข้อมูลที่เก็บไว้
        try:
            data = self.item_data.get(item_id)
            if not data: return
            table = data['table']
            record_id = data['record_id']
            description = self.tree.item(item_id, 'values')[3]
        except (KeyError, IndexError): return

        # เมื่อคลิกที่คอลัมน์ 'คำสั่ง' ให้ทำการลบได้เลย
        self.delete_record(table, record_id, description)

    def delete_record(self, table, record_id, description):
        """จัดการการลบข้อมูล"""
        confirm = messagebox.askyesno("ยืนยันการลบ",
                                      f"คุณต้องการลบรายการนี้ใช่หรือไม่?\n\n'{description}'\n\n"
                                      "การกระทำนี้จะส่งผลต่อข้อมูลที่เกี่ยวข้องและไม่สามารถย้อนกลับได้!",
                                      parent=self)
        if not confirm:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # --- จัดการ Logic การลบตามประเภทของตาราง ---
                if table == 'sales':
                    # 1. ดึงข้อมูลการขายเพื่อคืนจำนวนหุ้นกลับไปที่ lot
                    cursor.execute("SELECT lot_id, sell_volume FROM sales WHERE sale_id = ?", (record_id,))
                    sale_data = cursor.fetchone()
                    if sale_data:
                        lot_number, sell_volume = sale_data # lot_id ใน sales คือ lot_number
                        # 2. อัปเดตตาราง lots: เพิ่ม remaining_volume และเปลี่ยน status เป็น OPEN
                        cursor.execute("""
 UPDATE lots
 SET remaining_volume = remaining_volume + ?,
 status = 'OPEN'
 WHERE lot_number = ?
 """, (sell_volume, lot_number))

                elif table == 'lots':
                    # record_id คือ lot_id (PK) ของตาราง lots
                    # ต้องหา lot_number ก่อนเพื่อไปเช็คในตารางอื่น
                    cursor.execute("SELECT lot_number FROM lots WHERE lot_id = ?", (record_id,))
                    lot_res = cursor.fetchone()
                    if not lot_res:
                        return # ไม่พบข้อมูล
                    lot_number = lot_res[0]

                    # ตรวจสอบว่ามีรายการขายที่ผูกกับ lot นี้หรือไม่
                    cursor.execute("SELECT COUNT(*) FROM sales WHERE lot_id = ?", (lot_number,))
                    sale_count = cursor.fetchone()[0]
                    if sale_count > 0:
                        messagebox.showerror("ไม่สามารถลบได้",
                                             "ไม่สามารถลบรายการซื้อนี้ได้ เนื่องจากมีรายการขายที่ผูกอยู่\n"
                                             "กรุณาลบรายการขายที่เกี่ยวข้องทั้งหมดก่อน", parent=self)
                        return
                    # ถ้าไม่มีรายการขาย ก็สามารถลบรายการปันผล/คืนทุนที่เกี่ยวข้องได้
                    cursor.execute("DELETE FROM dividends WHERE lot_id = ?", (lot_number,))
                    cursor.execute("DELETE FROM capital_returns WHERE lot_id = ?", (lot_number,))

                # --- ทำการลบรายการหลัก ---
                # ใช้ f-string อย่างระมัดระวัง เพราะชื่อตารางมาจากโค้ดของเราเอง ไม่ใช่ input จาก user
                # หาชื่อคอลัมน์ Primary Key ของตารางนั้นๆ
                pk_column_map = {'lots': 'lot_id', 'sales': 'sale_id', 'dividends': 'id', 'capital_returns': 'id'}
                pk_column = pk_column_map.get(table)

                if pk_column:
                    cursor.execute(f"DELETE FROM {table} WHERE {pk_column} = ?", (record_id,))
                else:
                    raise ValueError(f"ไม่รู้จักตาราง '{table}'")

                conn.commit()
                messagebox.showinfo("สำเร็จ", "ลบรายการเรียบร้อยแล้ว", parent=self)

        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการลบข้อมูล: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("เกิดข้อผิดพลาด", f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}", parent=self)
        finally:
            # โหลดข้อมูลใหม่เพื่อแสดงผลล่าสุด
            self.load_transaction_log()

    def _update_statusbar(self, text):
        """อัปเดตข้อความใน Status bar"""
        chmodule.ChClass.status_bar(text, self)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_path_arg = sys.argv[1]
        app = StockLogApp(db_path_arg)
        app.mainloop()
    else:




        # สร้างหน้าต่างชั่วคราวเพื่อแสดงข้อความ
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("เกิดข้อผิดพลาด", "ไม่ได้ระบุไฟล์ฐานข้อมูล\nกรุณาเปิดโปรแกรมนี้ผ่านหน้าต่างหลัก")

    