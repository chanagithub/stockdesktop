import tkinter as tk
from chwidgets import CustomWidgets
import chwidgets


root = tk.Tk()
root.title("Custom Widgets Demo")
root.geometry("400x400")
root.configure(bg="#ecf0f1")

widgets = chwidgets.CustomWidgets(root, bg="#ecf0f1")

# ปุ่มขอบมน
widgets.rounded_button(text="Click Me", x=50, y=50)

# Textbox
widgets.textbox()

# Combobox
widgets.combobox(values=["Option 1", "Option 2", "Option 3"])

# Checkbox
widgets.checkbox(text="Accept Terms")

# Radiobutton
var = tk.IntVar()
widgets.radiobutton(text="Choice A", variable=var, value=1)
widgets.radiobutton(text="Choice B", variable=var, value=2)

# Listbox
widgets.listbox(items=["Item 1", "Item 2", "Item 3"])

root.mainloop()
