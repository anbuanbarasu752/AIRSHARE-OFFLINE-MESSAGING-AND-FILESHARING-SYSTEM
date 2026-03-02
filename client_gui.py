import socket
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk
from datetime import datetime
import os

HOST = "10.55.216.252"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# -------- LOGIN --------
temp_root = tk.Tk()
temp_root.withdraw()
username = simpledialog.askstring("Login", "Enter your name:")
temp_root.destroy()

client.send(f"JOIN:{username}".encode())

# -------- CHAT HISTORY FILE --------
history_file = open("chat_history.txt", "a", encoding="utf-8")

# -------- GUI --------
root = tk.Tk()
root.title("AirShare LAN Chat")
root.geometry("500x620")
root.configure(bg="#1e1e1e")

chat_area = tk.Text(root, bg="#2b2b2b", fg="white")
chat_area.pack(padx=10, pady=10, fill="both", expand=True)

entry = tk.Entry(root, bg="#3c3f41", fg="white")
entry.pack(padx=10, pady=5, fill="x")

preview_label = tk.Label(root, bg="#1e1e1e")
preview_label.pack()

user_count_label = tk.Label(root, text="Online Users: 1", bg="#1e1e1e", fg="lightgreen")
user_count_label.pack()

selected_file = None
online_users = 1

# -------- SEND MESSAGE --------
def send_message(event=None):
    message = entry.get()
    if message:
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"{timestamp}|{username}|{message}"
        client.send(f"MSG:{full_message}".encode())
        entry.delete(0, tk.END)

entry.bind("<Return>", send_message)

# -------- CHOOSE FILE --------
def choose_file():
    global selected_file
    file_path = filedialog.askopenfilename()

    if file_path:
        selected_file = file_path

        try:
            img = Image.open(file_path)
            img.thumbnail((150,150))
            img_tk = ImageTk.PhotoImage(img)
            preview_label.config(image=img_tk, text='')
            preview_label.image = img_tk
        except:
            preview_label.config(text="File Selected")

# -------- SEND FILE --------
def send_file():
    global selected_file
    if selected_file:
        filename = os.path.basename(selected_file)

        with open(selected_file, "rb") as f:
            file_data = f.read()

        header = f"FILE:{filename}:{len(file_data)}"
        client.send(header.encode())
        client.sendall(file_data)

        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] You sent file: {filename}\n"
        chat_area.insert(tk.END, message)
        chat_area.see(tk.END)

        history_file.write(message)
        history_file.flush()

        selected_file = None
        preview_label.config(image='')
        preview_label.config(text='')

# -------- RECEIVE --------
def receive_messages():
    global online_users
    while True:
        try:
            header = client.recv(1024).decode()

            if header.startswith("JOIN:"):
                user = header[5:]
                if user != username:
                    online_users += 1
                msg = f"🔵 {user} joined the chat\n"
                chat_area.insert(tk.END, msg)
                user_count_label.config(text=f"Online Users: {online_users}")
                history_file.write(msg)

            elif header.startswith("LEFT:"):
                user = header[5:]
                online_users -= 1
                msg = f"🔴 {user} left the chat\n"
                chat_area.insert(tk.END, msg)
                user_count_label.config(text=f"Online Users: {online_users}")
                history_file.write(msg)

            elif header.startswith("MSG:"):
                data = header[4:]
                time, user, message = data.split("|", 2)
                msg = f"[{time}] {user}: {message}\n"
                chat_area.insert(tk.END, msg)
                history_file.write(msg)

            elif header.startswith("FILE:"):
                parts = header.split(":")
                filename = parts[1]
                filesize = int(parts[2])

                file_data = b""
                while len(file_data) < filesize:
                    chunk = client.recv(4096)
                    file_data += chunk

                with open("received_" + filename, "wb") as f:
                    f.write(file_data)

                timestamp = datetime.now().strftime("%H:%M:%S")
                msg = f"[{timestamp}] File received: {filename}\n"
                chat_area.insert(tk.END, msg)
                history_file.write(msg)

            chat_area.see(tk.END)
            history_file.flush()

        except:
            break

threading.Thread(target=receive_messages, daemon=True).start()

# -------- BUTTONS --------
send_btn = tk.Button(root, text="Send", command=send_message, bg="#007acc", fg="white")
send_btn.pack(pady=5)

file_btn = tk.Button(root, text="Choose Image/File", command=choose_file, bg="#007acc", fg="white")
file_btn.pack(pady=5)

file_send_btn = tk.Button(root, text="Send File", command=send_file, bg="#007acc", fg="white")
file_send_btn.pack(pady=5)

# -------- CLOSE HANDLER --------
def on_closing():
    client.send(f"LEFT:{username}".encode())
    history_file.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()