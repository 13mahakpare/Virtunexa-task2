import os
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from datetime import datetime

# Database & Output Setup
DB_FILE = "history.db"
OUTPUT_FOLDER = "output images"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Create database table
def setup_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

setup_database()

# Tkinter UI Setup
root = tk.Tk()
root.title("Watermarking Tool")
root.geometry("700x600")
root.configure(bg="#2c3e50")

image_path = ""
watermark_path = ""

# Function to load an image
def load_image():
    global image_path
    image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    if image_path:
        display_image(image_path, img_label)
        update_preview()

# Function to load a watermark
def load_watermark():
    global watermark_path
    watermark_path = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")])
    if watermark_path:
        update_preview()

# Function to display images
def display_image(img_path, label):
    img = Image.open(img_path)
    img.thumbnail((250, 250))
    img = ImageTk.PhotoImage(img)
    label.config(image=img)
    label.image = img

# Function to update preview
def update_preview():
    global preview_label  # Ensure preview label is accessible

    if not image_path or not watermark_path:
        return

    try:
        image = Image.open(image_path).convert("RGBA")
        watermark = Image.open(watermark_path).convert("RGBA")
        watermark = watermark.resize((100, 100))

        # Apply opacity
        opacity = opacity_scale.get()
        r, g, b, alpha = watermark.split()
        alpha = alpha.point(lambda p: int(opacity * 255 / 100) if p > 0 else 0)  # Ensure correct opacity scaling
        watermark = Image.merge("RGBA", (r, g, b, alpha))

        # Define positions
        image_width, image_height = image.size
        positions = {
            "Top-Left": (10, 10),
            "Top-Right": (image_width - 110, 10),
            "Bottom-Left": (10, image_height - 110),
            "Bottom-Right": (image_width - 110, image_height - 110)
        }
        position = positions.get(position_var.get(), (10, 10))

        # Create a preview image
        preview = image.copy()
        preview.paste(watermark, position, watermark)

        # Resize preview without distorting aspect ratio
        preview.thumbnail((300, 300))  
        preview_img = ImageTk.PhotoImage(preview)

        # Update or create the preview label
        if 'preview_label' in globals() and preview_label.winfo_exists():
            preview_label.config(image=preview_img)
            preview_label.image = preview_img
        else:
            preview_label = tk.Label(root, image=preview_img, bg="#2c3e50")
            preview_label.image = preview_img
            preview_label.pack(pady=5)

    except Exception as e:
        print("Preview update error:", e)



# Function to apply watermark and save image
def apply_watermark():
    if not image_path or not watermark_path:
        messagebox.showerror("Error", "Please select an image and a watermark.")
        return

    image = Image.open(image_path).convert("RGBA")
    watermark = Image.open(watermark_path).convert("RGBA")
    watermark = watermark.resize((100, 100))

    opacity = opacity_scale.get()
    r, g, b, alpha = watermark.split()
    alpha = alpha.point(lambda p: opacity if p > 0 else 0)
    watermark = Image.merge("RGBA", (r, g, b, alpha))

    image_width, image_height = image.size
    position = {
        "Top-Left": (10, 10),
        "Top-Right": (image_width - 110, 10),
        "Bottom-Left": (10, image_height - 110),
        "Bottom-Right": (image_width - 110, image_height - 110)
    }[position_var.get()]

    transparent = Image.new("RGBA", image.size, (0, 0, 0, 0))
    transparent.paste(image, (0, 0))
    transparent.paste(watermark, position, watermark)

    output_path = os.path.join(OUTPUT_FOLDER, os.path.basename(image_path))
    if image_path.lower().endswith((".jpg", ".jpeg")):
        transparent = transparent.convert("RGB")

    transparent.save(output_path)

    # Save history
    save_to_history(output_path)

    messagebox.showinfo("Success", f"Watermark applied! Saved at:\n{output_path}")
    load_history()

# Function to save history
def save_to_history(file_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (file_name, timestamp) VALUES (?, ?)", 
                   (file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Function to load history
def load_history():
    history_tree.delete(*history_tree.get_children())
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT file_name, timestamp FROM history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        history_tree.insert("", "end", values=(row[1], os.path.basename(row[0])))

# Function to delete a selected image from history
def delete_history():
    selected_item = history_tree.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "Please select an image to delete.")
        return

    file_name = history_tree.item(selected_item, "values")[1]
    full_path = os.path.join(OUTPUT_FOLDER, file_name)

    confirm = messagebox.askyesno("Delete Confirmation", f"Are you sure you want to delete '{file_name}'?")
    if confirm:
        try:
            if os.path.exists(full_path):
                os.remove(full_path)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE file_name = ?", (full_path,))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Image deleted successfully!")
            load_history()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")

# UI Components
tk.Label(root, text="Watermarking Tool", font=("Arial", 18, "bold"), bg="#2c3e50", fg="white").pack(pady=10)

frame = tk.Frame(root, bg="#34495e", padx=20, pady=10)
frame.pack(pady=10, fill="x")

tk.Button(frame, text="Select Image", command=load_image, font=("Arial", 12), bg="#1abc9c", fg="white").grid(row=0, column=0, padx=10, pady=5)
img_label = tk.Label(frame, bg="#34495e")
img_label.grid(row=0, column=1, padx=10)

tk.Button(frame, text="Select Watermark", command=load_watermark, font=("Arial", 12), bg="#1abc9c", fg="white").grid(row=1, column=0, padx=10, pady=5)

# Opacity Scale with Gap Below
tk.Label(root, text="Opacity:", font=("Arial", 12), bg="#2c3e50", fg="white").pack()
opacity_scale = tk.Scale(root, from_=0, to=255, orient="horizontal", command=lambda x: update_preview(), bg="#2c3e50", fg="white")
opacity_scale.pack(pady=(0, 10))  # Added bottom padding for spacing

# Position Dropdown with Gap Above
tk.Label(root, text="Watermark Position:", font=("Arial", 12), bg="#2c3e50", fg="white").pack()
position_var = tk.StringVar(value="Top-Left")
tk.OptionMenu(root, position_var, "Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right", command=lambda x: update_preview()).pack(pady=(10, 5))

preview_label = tk.Label(root, bg="#2c3e50")
preview_label.pack()

tk.Button(root, text="Apply & Save", command=apply_watermark, font=("Arial", 14), bg="#e74c3c", fg="white").pack(pady=10)

# Frame for History Section & Delete Button (Centered)
history_frame = tk.Frame(root, bg="#2c3e50")
history_frame.pack(fill="x", pady=10)



# Adjust History Section to Stay Higher
history_frame = tk.Frame(root, bg="#2c3e50")
history_frame.pack(pady=5)  # Reduced spacing

history_tree = ttk.Treeview(history_frame, columns=("Time", "File"), show="headings", height=5)
history_tree.heading("Time", text="Timestamp")
history_tree.heading("File", text="File Name")
history_tree.pack(side="left", padx=10)

# Keep Delete Button Next to History, Not Below
delete_button = tk.Button(history_frame, text="Delete Selected", command=delete_history, font=("Arial", 12), bg="#c0392b", fg="white")
delete_button.pack(side="right", padx=10)

load_history()
root.mainloop()
