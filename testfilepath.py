
import tkinter as tk
from tkinter import filedialog
from find_saved_datafile_path import FindSavedDatafilePath
root = tk.Tk()
root.withdraw()  # ซ่อนหน้าต่างหลัก

finder = FindSavedDatafilePath()

folder_path = finder.get_pythonista_icloud_path()


if folder_path is None:
    print("Cannot find Pythonista iCloud folder")

else:
    print("FOUND PATH:")
    print(folder_path)

filename = filedialog.askopenfilename(
    parent=root,   # ใช้ root Tk เป็น parent
    initialdir=folder_path,
    title="เลือกไฟล์ Stock",
    filetypes=[("Stock files", "stock*.*")]
)
if filename:
    print("Selected file:", filename)
else:
    print("No file selected")

root.destroy()