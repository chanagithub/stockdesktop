import tkinter as tk
from secondwindows import SecondWindow

def open_second_window():
    # ซ่อนหน้าต่างหลักก่อน (ถ้าต้องการ)
    root.withdraw()
    # สร้างหน้าต่างที่สอง และส่ง root ไปด้วยเพื่อเรียกกลับมาได้
    SecondWindow(root)

root = tk.Tk()
root.title("Begin Window")
root.geometry("300x200")

btn = tk.Button(root, text="เปิดหน้าต่างที่สอง", command=open_second_window)
btn.pack(pady=50)

root.mainloop()