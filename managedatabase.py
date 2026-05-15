from sys import prefix
import tkinter as tk
from tkinter import ttk    
from tkinter import font as tkfont
from tkinter import filedialog, messagebox
import chmodule
import shutil
import os
import sqlite3
# นำเข้าโครงสร้างตารางจาก create_database.py โดยตรง
from create_database import (CREATE_LOTS_TABLE, CREATE_DIVIDENDS_TABLE, CREATE_CAPITAL_RETURNS_TABLE, CREATE_SALES_TABLE,
                             CREATE_WAITING_LOTS_TABLE)
class Appdb(tk.Toplevel):
    def __init__(self, parent, on_open_success=None):
        super().__init__(parent)
        self.title("จัดการฐานข้อมูล")
        self.parent = parent

        self.on_open_success_callback = on_open_success
        self.db_path = None # ประกาศ attribute db_path ไว้ล่วงหน้า

        #center windows
        chmodule.ChClass.setwindowcenter(self, 400, 200)
        self.status_bar = chmodule.ChClass.status_bar("Ready", self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)         
        self.create_widgets()   
        self.attributes('-topmost', True)
        self.create_menubar()

    def create_widgets(self):
        # Load custom font
        self.custom_font = tkfont.Font(family="Helvetica", size=12, weight="bold")

        self.label = ttk.Label(self, text="จัดการฐานข้อมูล", font=self.custom_font)
        self.label.pack(pady=(10, 5))

        chmodule.ChClass.create_canvas_buttons_center_for_data_management(self)

    def create_menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # --- Menu "การทำงาน" ---
        work_menu = tk.Menu(menubar, tearoff=0)
        work_menu.add_command(label="Create Database", command=lambda: self.create_database(""))
        work_menu.add_command(label="Open Database", command=self.open_database)
        work_menu.add_separator()
        work_menu.add_command(label="ออก", command=self.destroy)
        menubar.add_cascade(label="File", menu=work_menu)

    def create_database(self, inital_filename=None):
        """รับชื่อไฟล์และสร้างฐานข้อมูลในโฟลเดอร์ iCloud ที่กำหนดไว้เท่านั้น"""
        from tkinter import simpledialog
        
        # 1. กำหนดโฟลเดอร์เป้าหมาย (Locked Path)
        target_dir = '/Users/chanaimac/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/stockfundios'
        
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except Exception as e:
                messagebox.showerror("Error", f"ไม่สามารถเข้าถึงหรือสร้างโฟลเดอร์ได้:\n{e}", parent=self)
                return None

        self.deiconify()
        self.attributes('-topmost', True)

        # --- ส่วนที่เพิ่มใหม่: ถามว่าเป็น หุ้น หรือ กองทุน ---
        # ใช้ askyesnocancel: Yes = หุ้น, No = กองทุน, Cancel = ยกเลิก
        choice = messagebox.askyesnocancel(
            "เลือกประเภทฐานข้อมูล", 
            "คลิก 'Yes' สำหรับ หุ้น (stock)\nคลิก 'No' สำหรับ กองทุน (fund)", 
            parent=self
        )
        
        if choice is None: # กด Cancel
            return None
        
        # กำหนด Prefix ตามการเลือก
        auto_prefix = "stock" if choice is True else "fund"
        # ----------------------------------------------

        # 2. ถามชื่อไฟล์จากผู้ใช้
        db_name = simpledialog.askstring(
            "สร้างฐานข้อมูลใหม่", 
            f"ระบุชื่อต่อท้าย {auto_prefix} (เช่น mydata):", 
            parent=self
        )

        self.attributes('-topmost', False)
        
        if not db_name:
            messagebox.showinfo("ยกเลิก", "การสร้างฐานข้อมูลถูกยกเลิก", parent=self)
            return None

        # จัดการชื่อไฟล์: ตัดช่องว่างและทำให้นามสกุลถูกต้อง
        db_name = db_name.strip()
        if not db_name.lower().endswith('.db'):
            db_name += '.db'
            
        # ตรวจสอบว่าชื่อที่กรอกมามี prefix หรือยัง ถ้าไม่มีให้เติม auto_prefix เข้าไปข้างหน้า
        if not db_name.lower().startswith(auto_prefix):
            db_name = f"{auto_prefix}{db_name}"

        # รวม Path เข้าด้วยกัน
        new_db_path = os.path.join(target_dir, db_name)

        # 3. ตรวจสอบไฟล์ซ้ำ
        if os.path.exists(new_db_path):
            if not messagebox.askyesno("ยืนยัน", f"ไฟล์ '{db_name}' มีอยู่แล้ว คุณต้องการเขียนทับหรือไม่?", parent=self):
                return None

        # 4. สร้างไฟล์และ Schema
        try:
            with sqlite3.connect(new_db_path) as conn:
                schema_script = (f"{CREATE_LOTS_TABLE}\n{CREATE_DIVIDENDS_TABLE}\n"
                               f"{CREATE_CAPITAL_RETURNS_TABLE}\n{CREATE_SALES_TABLE}\n"
                               f"{CREATE_WAITING_LOTS_TABLE}")
                conn.executescript(schema_script)
                
            messagebox.showinfo("สำเร็จ", f"สร้างฐานข้อมูล {auto_prefix} สำเร็จที่:\n{new_db_path}", parent=self)
            self._update_statusbar(f"สร้างฐานข้อมูลสำเร็จ: {new_db_path}")
            self.destroy()
            return new_db_path

        except Exception as e:
            messagebox.showerror("เกิดข้อผิดพลาด", f"ไม่สามารถสร้างไฟล์ได้: {e}", parent=self)
            self._update_statusbar("การสร้างฐานข้อมูลล้มเหลว")
            return None

    def open_database(self, prefix=None):
        """Opens a file dialog to select an existing database and validates its schema."""
        # แสดงและตั้งค่า topmost ชั่วคราวก่อนเปิด filedialog
        self.deiconify()
        self.attributes('-topmost', True)

        filetypes = [("Database Files", "*.db"), ("All Files", "*.*")]
        if prefix:
            filetypes.insert(0, (f"{prefix} database files", f"{prefix}*.db"))

        filepath = filedialog.askopenfilename(
            parent=self,
            title="เปิดไฟล์ฐานข้อมูล",
            filetypes=filetypes
        )

        if not filepath:
            self._update_statusbar("การเปิดไฟล์ถูกยกเลิก")
            return

        if prefix and not os.path.basename(filepath).lower().startswith(prefix.lower()):
            messagebox.showwarning(
                "เลือกไฟล์ไม่ตรงประเภท",
                f"กรุณาเลือกไฟล์ฐานข้อมูลที่ขึ้นต้นด้วย '{prefix}'",
                parent=self
            )
            self.attributes('-topmost', False)
            self.deiconify()
            self._update_statusbar("เลือกไฟล์ไม่ตรงประเภท")
            return

        # ตรวจสอบความถูกต้องของโครงสร้างไฟล์
        is_valid, error_message = self._is_schema_valid(filepath)

        if is_valid:
            self._update_statusbar(f"ไฟล์ที่เลือก: {filepath}")
            # --- จุดแก้ไข: ย้าย withdraw() มาไว้ที่นี่ ---
            # ซ่อนหน้าต่างนี้หลังจากที่เลือกไฟล์และตรวจสอบสำเร็จแล้ว
            self.attributes('-topmost', False)
            self.withdraw()
            # --- จุดแก้ไข: เรียก callback function ถ้ามี ---
            if self.on_open_success_callback:
                self.on_open_success_callback(filepath)
            else:
                self._open_data_viewer_and_close(filepath)
        else:
            messagebox.showerror("ไฟล์ไม่ถูกต้อง", f"โครงสร้างของไฟล์ '{os.path.basename(filepath)}' ไม่ถูกต้อง\n\n{error_message}")
            # --- จุดแก้ไข: ยกเลิก topmost หากไฟล์ไม่ถูกต้อง ---
            self.attributes('-topmost', False)
            self.deiconify() # แสดงหน้าต่างค้างไว้เพื่อให้ผู้ใช้เห็นข้อผิดพลาด
            self._update_statusbar("เลือกไฟล์ที่โครงสร้างไม่ถูกต้อง")

    def _get_db_schema(self, db_path):
        """Helper function to get a comparable schema dump from a database."""
        if not os.path.exists(db_path):
            return None, f"ไม่พบไฟล์: {db_path}"
        try:
            with sqlite3.connect(db_path) as conn:
                # ดึงคำสั่ง CREATE ทั้งหมด ยกเว้นของตารางระบบ และเรียงตามชื่อเพื่อให้เปรียบเทียบได้
                schema_lines = [row[0] for row in conn.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY name")]
                return "\n".join(schema_lines), None
        except sqlite3.Error as e:
            return None, f"เกิดข้อผิดพลาด SQLite: {e}"

    def _get_expected_schema_from_scripts(self):
        """Generates the expected schema string from the CREATE_TABLE scripts."""
        try:
            # สร้างฐานข้อมูลในหน่วยความจำชั่วคราวเพื่อดึงโครงสร้างจากสคริปต์
            with sqlite3.connect(":memory:") as conn:
                schema_script = (f"{CREATE_LOTS_TABLE}\n{CREATE_DIVIDENDS_TABLE}\n"
                               f"{CREATE_CAPITAL_RETURNS_TABLE}\n{CREATE_SALES_TABLE}\n"
                               f"{CREATE_WAITING_LOTS_TABLE}")
                conn.executescript(schema_script)
                # ดึงคำสั่ง CREATE ทั้งหมด ยกเว้นของตารางระบบ และเรียงตามชื่อเพื่อให้เปรียบเทียบได้
                schema_lines = [row[0] for row in conn.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY name")]
                return "\n".join(schema_lines), None
        except sqlite3.Error as e:
            return None, f"เกิดข้อผิดพลาดในการสร้างโครงสร้างต้นแบบ: {e}"

    def _is_schema_valid(self, file_to_check):
        """
        Validates if the schema of the selected file matches the template schema.
        Returns (True, None) if valid, or (False, error_message) if not.
        """
        # 1. ดึงโครงสร้างที่คาดหวังจากสคริปต์ CREATE TABLE โดยตรง
        template_schema, error = self._get_expected_schema_from_scripts()
        if error:
            return False, f"ไม่สามารถสร้างโครงสร้างต้นแบบได้: {error}"

        # 2. ดึงโครงสร้างจากไฟล์ที่ผู้ใช้เลือก
        user_schema, error = self._get_db_schema(file_to_check)
        if error:
            return False, f"ไม่สามารถอ่านไฟล์ที่เลือกได้: {error}"

        # 3. เปรียบเทียบโครงสร้าง
        return (template_schema == user_schema), "โครงสร้างตารางไม่ตรงกับต้นแบบ"

    def _open_data_viewer_and_close(self, db_path):
        """ซ่อนหน้าต่างปัจจุบัน, เปิด DataViewer, และตั้งค่าให้ปิดโปรแกรมเมื่อ DataViewer ถูกปิด"""
        self.withdraw() # ซ่อนหน้าต่าง Appdb
        viewer = DataViewer(self, db_path)
        # เมื่อหน้าต่าง viewer ถูกปิด (โปรโตคอล "WM_DELETE_WINDOW") ให้เรียก self.destroy
        # เพื่อปิดหน้าต่าง Appdb ที่ซ่อนอยู่และจบการทำงานของโปรแกรม
        viewer.protocol("WM_DELETE_WINDOW", self.destroy)

    def _update_statusbar(self, text):
        """Internal method to update the status bar text."""
        chmodule.ChClass.status_bar(text, self)

    def create_button(self, x, y, width, height, text, tooltip_text):
        command = None
        if y == 10: # สร้างฐานข้อมูลใหม่
            command = lambda: self.create_database("")
        elif y == 50: # เปิดไฟล์ฐานข้อมูล
            command = lambda: self.open_database()
        elif y == 90: # ปิดโปรแกรม
            command = lambda:self.quit()
        # เรียกใช้ฟังก์ชัน on_close ที่จัดการปิดทุกอย่าง

        button = ttk.Button(self, text=text, command=command)
        button.place(x=x, y=y, width=width, height=height)
        button.bind("<Enter>", lambda event: self._update_statusbar(tooltip_text))
        button.bind("<Leave>", lambda event: self._update_statusbar("Ready"))

    def fetch_one(self, query, params=()):
        """ดึงข้อมูลแถวเดียวจากฐานข้อมูล"""
        if not self.db_path:
            raise Exception("ไม่ได้เชื่อมต่อกับฐานข้อมูล")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการ fetch_one: {e}")
            return None

    def fetch_all(self, query, params=()):
        """ดึงข้อมูลทั้งหมดจากฐานข้อมูล"""
        if not self.db_path:
            raise Exception("ไม่ได้เชื่อมต่อกับฐานข้อมูล")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการ fetch_all: {e}")
            return []




class DataViewer(tk.Toplevel):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db_path = db_path
        self.title(f"ข้อมูลจาก: {os.path.basename(db_path)}")
        
        # ขยายขนาดหน้าต่างและจัดกึ่งกลาง
        window_width = 1200
        window_height = 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self._create_widgets()
        self._load_table_list()

    def _create_widgets(self):
        """สร้าง Layout หลัก, รายชื่อตาราง, และส่วนแสดงข้อมูล"""
        # 1. สร้าง PanedWindow เพื่อให้แบ่งขนาดได้
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 2. สร้าง Frame ด้านซ้ายสำหรับ Listbox ของตาราง
        tables_frame = ttk.Frame(paned_window, padding=5)
        tables_frame.rowconfigure(1, weight=1)
        tables_frame.columnconfigure(0, weight=1)
        paned_window.add(tables_frame, weight=1) # weight=1 กำหนดสัดส่วนเริ่มต้น

        ttk.Label(tables_frame, text="ตารางทั้งหมด", font=("Helvetica", 12, "bold")).grid(row=0, column=0, pady=(0, 5), sticky='w')
        self.table_listbox = tk.Listbox(tables_frame, exportselection=False)
        self.table_listbox.grid(row=1, column=0, sticky='nsew')
        self.table_listbox.bind("<<ListboxSelect>>", self._on_table_select)

        # 3. สร้าง Frame ด้านขวาสำหรับ Treeview แสดงข้อมูล
        data_frame = ttk.Frame(paned_window, padding=5)
        data_frame.rowconfigure(0, weight=1)
        data_frame.columnconfigure(0, weight=1)
        paned_window.add(data_frame, weight=4) # weight=4 ให้พื้นที่มากกว่า

        self.tree = ttk.Treeview(data_frame, show='headings')
        
        # --- Scrollbars สำหรับ Treeview ---
        vsb = ttk.Scrollbar(data_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(data_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

    def _load_table_list(self):
        """ดึงรายชื่อตารางจากฐานข้อมูลและแสดงใน Listbox"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
                tables = cursor.fetchall()
                for table in tables:
                    self.table_listbox.insert(tk.END, table[0])
        except sqlite3.Error as e:
            messagebox.showerror("เกิดข้อผิดพลาด", f"ไม่สามารถอ่านรายชื่อตารางได้:\n{e}", parent=self)

    def _on_table_select(self, event):
        """ทำงานเมื่อผู้ใช้คลิกเลือกตารางใน Listbox"""
        # ดึงรายการที่เลือก
        selected_indices = self.table_listbox.curselection()
        if not selected_indices:
            return
        
        table_name = self.table_listbox.get(selected_indices[0])
        self._display_table_data(table_name)

    def _display_table_data(self, table_name):
        """เชื่อมต่อฐานข้อมูล, ดึงข้อมูลจากตารางที่ระบุ, และแสดงผลใน Treeview"""
        # --- ล้างข้อมูลและคอลัมน์เก่าใน Treeview ---
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # --- ใช้ f-string อย่างปลอดภัย (เพราะชื่อตารางมาจาก DB เอง) ---
                cursor.execute(f"SELECT * FROM \"{table_name}\"")

                # --- ตั้งค่าคอลัมน์ของ Treeview จากข้อมูลของ cursor ---
                column_names = [description[0] for description in cursor.description]
                if not column_names: return # ถ้าตารางไม่มีข้อมูล
                
                self.tree["columns"] = column_names
                for col in column_names:
                    self.tree.heading(col, text=col, command=lambda _col=col: self._sort_column(_col, False))
                    self.tree.column(col, width=120, anchor='w')

                # --- เพิ่มข้อมูลลงใน Treeview ---
                for row in cursor.fetchall():
                    self.tree.insert("", "end", values=row)

        except sqlite3.Error as e:
            messagebox.showerror("เกิดข้อผิดพลาดในการอ่านข้อมูล", f"ไม่สามารถดึงข้อมูลจากตาราง '{table_name}' ได้:\n{e}", parent=self)

    def _sort_column(self, col, reverse):
        """เรียงข้อมูลในคอลัมน์เมื่อคลิกที่ Header"""
        data_list = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        # ลองแปลงเป็นตัวเลขเพื่อเรียงลำดับให้ถูกต้อง
        try:
            data_list.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            data_list.sort(key=lambda t: t[0], reverse=reverse)

        for index, (val, k) in enumerate(data_list):
            self.tree.move(k, '', index)

        # สลับการเรียงลำดับในครั้งต่อไป
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

if __name__ == "__main__":
    app = Appdb()
    # สร้าง root window ชั่วคราวสำหรับทดสอบ
    root = tk.Tk()
    root.withdraw() 
    app = Appdb(parent=root)
    app.mainloop()
