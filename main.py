import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

# === Adatbázis inicializálás ===
conn = sqlite3.connect("library.db")
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,
    title TEXT,
    author TEXT,
    isbn TEXT UNIQUE,
    genre TEXT,
    is_borrowed INTEGER DEFAULT 0
)
''')
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT
)
''')
c.execute('''
CREATE TABLE IF NOT EXISTS borrows (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    book_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(book_id) REFERENCES books(id)
)
''')
conn.commit()
conn.close()

# === GUI ===
root = tk.Tk()
root.title("Könyvtári rendszer")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# === Tabok létrehozása ===
tab_names = ["Könyv felvitel", "Felhasználó felvitel", "Kölcsönzés", "Visszavétel", "Keresés", "Könyv törlése", "Felhasználó törlése", "Info"]
tabs = {}
for name in tab_names:
    tabs[name] = ttk.Frame(notebook)
    notebook.add(tabs[name], text=name)

# === Könyv felvitel ===
def add_book():
    title = book_title.get()
    author = book_author.get()
    isbn = book_isbn.get()
    genre = book_genre.get()

    if not (title and author and isbn and genre):
        messagebox.showerror("Hiba", "Minden mezőt ki kell tölteni.")
        return

    try:
        conn = sqlite3.connect("library.db")
        c = conn.cursor()
        c.execute("INSERT INTO books (title, author, isbn, genre) VALUES (?, ?, ?, ?)", (title, author, isbn, genre))
        conn.commit()
        conn.close()
        messagebox.showinfo("Siker", "Könyv hozzáadva.")
        book_title.delete(0, tk.END)
        book_author.delete(0, tk.END)
        book_isbn.delete(0, tk.END)
        book_genre.delete(0, tk.END)
        refresh_borrow_data()
        refresh_delete_books_list()
    except sqlite3.IntegrityError:
        messagebox.showerror("Hiba", "Ez az ISBN már szerepel.")

book_title = tk.Entry(tabs["Könyv felvitel"])
book_author = tk.Entry(tabs["Könyv felvitel"])
book_isbn = tk.Entry(tabs["Könyv felvitel"])
book_genre = tk.Entry(tabs["Könyv felvitel"])
tk.Label(tabs["Könyv felvitel"], text="Cím").pack()
book_title.pack()
tk.Label(tabs["Könyv felvitel"], text="Szerző").pack()
book_author.pack()
tk.Label(tabs["Könyv felvitel"], text="ISBN").pack()
book_isbn.pack()
tk.Label(tabs["Könyv felvitel"], text="Műfaj").pack()
book_genre.pack()
tk.Button(tabs["Könyv felvitel"], text="Könyv hozzáadása", command=add_book).pack(pady=10)

# === Felhasználó felvitel ===
def add_user():
    name = user_name.get()
    if not name:
        messagebox.showerror("Hiba", "Adj meg egy nevet.")
        return
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    user_name.delete(0, tk.END)
    messagebox.showinfo("Siker", "Felhasználó hozzáadva.")
    refresh_borrow_data()
    refresh_delete_users_list()

user_name = tk.Entry(tabs["Felhasználó felvitel"])
tk.Label(tabs["Felhasználó felvitel"], text="Név").pack()
user_name.pack()
tk.Button(tabs["Felhasználó felvitel"], text="Felhasználó hozzáadása", command=add_user).pack(pady=10)

# === Kölcsönzés ===
book_combo = ttk.Combobox(tabs["Kölcsönzés"])
user_combo = ttk.Combobox(tabs["Kölcsönzés"])

def borrow_book():
    book = book_combo.get()
    user = user_combo.get()
    if not (book and user):
        messagebox.showerror("Hiba", "Válassz könyvet és felhasználót.")
        return
    isbn = book.split(" - ")[0]
    user_id = user.split(" - ")[0]
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("SELECT id FROM books WHERE isbn=? AND is_borrowed=0", (isbn,))
    result = c.fetchone()
    if not result:
        messagebox.showerror("Hiba", "A könyv nem elérhető.")
        conn.close()
        return
    book_id = result[0]
    c.execute("INSERT INTO borrows (user_id, book_id) VALUES (?, ?)", (user_id, book_id))
    c.execute("UPDATE books SET is_borrowed=1 WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    messagebox.showinfo("Siker", "Kölcsönzés rögzítve.")
    refresh_borrow_data()

tk.Label(tabs["Kölcsönzés"], text="Könyv").pack()
book_combo.pack()
tk.Label(tabs["Kölcsönzés"], text="Felhasználó").pack()
user_combo.pack()
tk.Button(tabs["Kölcsönzés"], text="Kölcsönöz", command=borrow_book).pack(pady=10)

# === Visszavétel ===
borrowed_combo = ttk.Combobox(tabs["Visszavétel"])

def return_book():
    selected = borrowed_combo.get()
    if not selected:
        messagebox.showerror("Hiba", "Válassz egy könyvet.")
        return
    borrow_id = selected.split(" - ")[0]
    book_id = selected.split(" - ")[1]
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("DELETE FROM borrows WHERE id=?", (borrow_id,))
    c.execute("UPDATE books SET is_borrowed=0 WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    messagebox.showinfo("Siker", "Könyv visszavéve.")
    refresh_borrow_data()

tk.Label(tabs["Visszavétel"], text="Kölcsönzött könyvek").pack()
borrowed_combo.pack()
tk.Button(tabs["Visszavétel"], text="Visszavétel", command=return_book).pack(pady=10)

# === Keresés ===
search_entry = tk.Entry(tabs["Keresés"])
search_result = tk.Text(tabs["Keresés"], height=10, width=60)

def search_books():
    query = search_entry.get()
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("SELECT title, author, isbn, genre FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR genre LIKE ?",
              (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
    results = c.fetchall()
    conn.close()
    search_result.delete(1.0, tk.END)
    if results:
        for r in results:
            search_result.insert(tk.END, f"Cím: {r[0]}, Szerző: {r[1]}, ISBN: {r[2]}, Műfaj: {r[3]}\n")
    else:
        search_result.insert(tk.END, "Nincs találat.")

tk.Label(tabs["Keresés"], text="Keresés név, ISBN, szerző vagy műfaj alapján").pack()
search_entry.pack()
tk.Button(tabs["Keresés"], text="Keresés", command=search_books).pack(pady=5)
search_result.pack()

# === Könyv törlése tab ===
delete_book_listbox = tk.Listbox(tabs["Könyv törlése"], width=60)
delete_book_listbox.pack(padx=10, pady=10)

def refresh_delete_books_list():
    delete_book_listbox.delete(0, tk.END)
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("SELECT id, title, author FROM books")
    for row in c.fetchall():
        delete_book_listbox.insert(tk.END, f"{row[0]} - {row[1]} by {row[2]}")
    conn.close()

def delete_selected_book():
    selected = delete_book_listbox.curselection()
    if not selected:
        messagebox.showerror("Hiba", "Válassz egy könyvet a törléshez.")
        return
    book_id = int(delete_book_listbox.get(selected[0]).split(" - ")[0])
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    messagebox.showinfo("Siker", "Könyv törölve.")
    refresh_delete_books_list()
    refresh_borrow_data()

tk.Button(tabs["Könyv törlése"], text="Könyv törlése", command=delete_selected_book).pack(pady=5)

# === Felhasználó törlése tab ===
delete_user_listbox = tk.Listbox(tabs["Felhasználó törlése"], width=40)
delete_user_listbox.pack(padx=10, pady=10)

def refresh_delete_users_list():
    delete_user_listbox.delete(0, tk.END)
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM users")
    for row in c.fetchall():
        delete_user_listbox.insert(tk.END, f"{row[0]} - {row[1]}")
    conn.close()

def delete_selected_user():
    selected = delete_user_listbox.curselection()
    if not selected:
        messagebox.showerror("Hiba", "Válassz egy felhasználót a törléshez.")
        return
    user_id = int(delete_user_listbox.get(selected[0]).split(" - ")[0])
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    # Kölcsönzéseket is töröljük hozzá
    c.execute("DELETE FROM borrows WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    messagebox.showinfo("Siker", "Felhasználó törölve.")
    refresh_delete_users_list()
    refresh_borrow_data()

tk.Button(tabs["Felhasználó törlése"], text="Felhasználó törlése", command=delete_selected_user).pack(pady=5)

# === Info fül tartalma ===
info_label = tk.Label(
    tabs["Info"],
    text="Készítette: Makai István\nÉv: 2025\nEmail: istvan.makai@gmail.com",
    justify="center",
    font=("Arial", 12),
    pady=20
)
info_label.pack(expand=True)

# === Helper függvény a kölcsönzéshez való frissítéshez ===
def refresh_borrow_data():
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("SELECT isbn, title FROM books WHERE is_borrowed=0")
    books = c.fetchall()
    book_combo['values'] = [f"{isbn} - {title}" for isbn, title in books]

    c.execute("SELECT id, name FROM users")
    users = c.fetchall()
    user_combo['values'] = [f"{id} - {name}" for id, name in users]

    c.execute('''
    SELECT borrows.id, books.id, books.title FROM borrows 
    JOIN books ON borrows.book_id=books.id
    ''')
    borrows = c.fetchall()
    borrowed_combo['values'] = [f"{borrow_id} - {book_id} - {title}" for borrow_id, book_id, title in borrows]

    conn.close()

# Első frissítés
refresh_borrow_data()
refresh_delete_books_list()
refresh_delete_users_list()

root.mainloop()
