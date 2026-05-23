import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime


def get_photo_datetime(filepath):
    try:
        image = Image.open(filepath)
        exif_data = image._getexif()
        if not exif_data:
            return None
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'DateTimeOriginal':
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None
    return None


def format_new_filename(date_obj, ext, existing_names):
    base_name = date_obj.strftime("%H%M%S_%Y%m%d")
    new_name = f"{base_name}{ext}"
    counter = 1
    while new_name in existing_names:
        new_name = f"{base_name}_{counter}{ext}"
        counter += 1
    return new_name


def select_and_rename():
    folder = filedialog.askdirectory()
    if not folder:
        return

    files = [f for f in os.listdir(folder)
             if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    photos_with_dates = []
    for f in files:
        path = os.path.join(folder, f)
        date_taken = get_photo_datetime(path)
        if date_taken:
            photos_with_dates.append((f, date_taken))

    if not photos_with_dates:
        messagebox.showinfo("Aviso", "Nenhuma imagem com data EXIF encontrada.")
        return

    photos_with_dates.sort(key=lambda x: x[1])

    total = len(photos_with_dates)
    progress["maximum"] = total
    progress["value"] = 0
    counter_label.config(text="0 / " + str(total))

    existing_names = set(os.listdir(folder))
    renamed = 0

    for original_name, date in photos_with_dates:
        original_path = os.path.join(folder, original_name)
        ext = os.path.splitext(original_name)[1].lower()
        new_name = format_new_filename(date, ext, existing_names)
        new_path = os.path.join(folder, new_name)

        os.rename(original_path, new_path)
        existing_names.add(new_name)

        renamed += 1
        progress["value"] = renamed
        counter_label.config(text=f"{renamed} / {total}")
        root.update_idletasks()

    messagebox.showinfo(
        "Sucesso",
        f"{renamed} fotos renomeadas com sucesso."
    )


# ================= GUI =================

root = tk.Tk()
root.title("Organizar Fotos por Data e Hora")
root.configure(bg="#FFA500")
root.resizable(False, False)

# Centralizar janela
window_width = 450
window_height = 230
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

frame = tk.Frame(root, bg="#FFA500")
frame.pack(expand=True, fill="both")

btn = tk.Button(
    frame,
    text="Selecionar Pasta e Organizar",
    command=select_and_rename,
    width=28,
    height=2,
    bg="#2ECC71",
    fg="white",
    activebackground="#27AE60",
    activeforeground="white",
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    cursor="hand2"
)
btn.pack(pady=20)

progress = ttk.Progressbar(
    frame,
    orient="horizontal",
    length=320,
    mode="determinate"
)
progress.pack(pady=10)

counter_label = tk.Label(
    frame,
    text="0 / 0",
    bg="#FFA500",
    fg="black",
    font=("Segoe UI", 10, "bold")
)
counter_label.pack()

root.mainloop()
