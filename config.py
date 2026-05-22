# config.py
import platform
from tkinter import font

def setup_global_fonts():
    # กำหนดค่าตาม OS
    if platform.system() == "Darwin":  # macOS
        font_config = {"family": "Helvetica Neue", "size": 14}
    else:  # Windows / Linux
        font_config = {"family": "Segoe UI", "size": 11}
    
    # ตั้งค่าฟอนต์เริ่มต้นของระบบ
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family=font_config["family"], size=font_config["size"])
    
    # ตั้งค่าฟอนต์อื่นๆ เพิ่มเติมถ้าต้องการ
    text_font = font.nametofont("TkTextFont")
    text_font.configure(family=font_config["family"], size=font_config["size"])