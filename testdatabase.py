import tkinter as tk
from tkinter import messagebox
import sqlite3
import chmodule # Assuming chmodule is a custom module for character handling   


# Create the database and table if not exists

# Set up the GUI
class root (tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Character Database")
        self.geometry("400x300")
        chmodule.ChClass.setwindowcenter(self, 400, 300)
        self.create_database("characters.db")
        self.create_widgets()

    def create_widgets(self):

        self.label_title = tk.Label(self, text="Character Database Management")
        self.label_title.pack(pady=10)

        # Create labels and entry fields            
        self.label_name = tk.Label(self, text="Name:")
        self.label_name.pack()
        self.entry_name = tk.Entry(self)
        self.entry_name.pack()

        self.label_class = tk.Label(self, text="Class:")
        self.label_class.pack()
        self.entry_class = tk.Entry(self)
        self.entry_class.pack()

        self.label_level = tk.Label(self, text="Level:")
        self.label_level.pack()
        self.entry_level = tk.Entry(self)
        self.entry_level.pack()

        self.button_add = tk.Button(self, text="Add Character", command=self.on_add_character)
        self.button_add.pack()

        self.button_view = tk.Button(self, text="View Characters", command=self.on_view_characters)
        self.button_view.pack()

    def create_database(self, db_name):
        with sqlite3.connect(db_name) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS characters
                        (id INTEGER PRIMARY KEY, name TEXT, class TEXT, level INTEGER)''')
            conn.commit()

    def add_character(self, name, char_class, level):
        name = name.strip()
        char_class = char_class.strip()
        try:
            level_int = int(level)
            if not name or not char_class or level_int < 1:
                messagebox.showerror("Error", "Invalid character details.")
                return
            
            with sqlite3.connect('characters.db') as conn:
                c = conn.cursor()
                c.execute("INSERT INTO characters (name, class, level) VALUES (?, ?, ?)", 
                          (name, char_class, level_int))
                conn.commit()
            return True
        except ValueError:
            messagebox.showerror("Error", "Level must be a number.")
            return False

    def view_characters(self):
        with sqlite3.connect('characters.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM characters")
            return c.fetchall()

    def on_add_character(self): 
        name = self.entry_name.get()
        char_class = self.entry_class.get()
        level = self.entry_level.get()
        if self.add_character(name, char_class, level):
            messagebox.showinfo("Success", "Character added successfully!")
            self.entry_name.delete(0, tk.END)
            self.entry_class.delete(0, tk.END)
            self.entry_level.delete(0, tk.END)

    def on_view_characters(self):
        characters = self.view_characters()
        display_text = "\n".join([f"ID: {row[0]}, Name: {row[1]}, Class: {row[2]}, Level: {row[3]}" for row in characters])
        messagebox.showinfo("Character List", display_text if display_text else "No characters found.")

if __name__ == "__main__":
    app = root()
    app.mainloop()
    
