import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import json
import ipaddress
from base_station import BaseStation
import traceback

def switch_bs_mode(*args):
    mode = mode_var.get()
    if mode == "Auto":	
        bs.mode = 'detect' 
        bs.send_command("mode-auto")
    elif mode == "Manual":
        bs.mode = 'manual'
        bs.send_command("mode-manual")

def on_connect():
    global bs
    try:
        ip_address = str(ipaddress.ip_address(ip_entry.get()))	
        print(f"Valid ip address: {ip_address}")
        bs.connect(host=ip_address, port=65432)
        show_start_sreen(False)
        show_work_screen()
    except ValueError:
        messagebox.showerror("Unable to connect", f"No server is listening at '{ip_entry.get()}'")
    except Exception as e:
        messagebox.showerror("Error", str(e))
        traceback.print_exc()

def on_disconnect():
    if messagebox.askokcancel("Disconnect", "Do you want to disconnect and close the application?"):
        bs.send_command("disconnect")
        bs.close()
        root.destroy()

def on_manual(event):
    if bs.mode == 'manual':
        if event.keysym == "Left":
            bs.send_command("manual-left")
        elif event.keysym == "Right":
            bs.send_command("manual-right")
        elif event.keysym == "Up":
            bs.send_command("manual-forward")
        elif event.keysym == 's':
            bs.send_command("manual-stop")
        elif event.keysym == 'x':
            bs.send_command("manual-backward")

def on_shutdown():
    if messagebox.askokcancel("Shutdown", "Do you want to shutdown the boat and close the application?"):
        bs.send_command("shutdown")
        bs.close()
        root.destroy()

# Init base station
bs = BaseStation()

root = tk.Tk()
root.title("Base Station v0.1")
root.geometry("960x720")

canvas = tk.Canvas(root, width=960, height=720)

work_frame = tk.Frame(root)

# IP address input and Connect button
welcome_label = tk.Label(canvas, text="Welcome on board, Captain Kurt!") 
ip_label = tk.Label(canvas, text="Please enter vehicle's ip address to connect")
ip_entry = tk.Entry(canvas)
connect_button = tk.Button(canvas, text="Connect", command=on_connect)

# Create wallpaper label
bg_image = Image.open("config/wallpaper.jpg") 
bg_image = bg_image.resize((960, 720))
bg_image = ImageTk.PhotoImage(bg_image)
canvas.create_image(0, 0, anchor=tk.NW, image=bg_image)

canvas.create_window(365, 95, anchor=tk.NW, window=welcome_label)
canvas.create_window(340, 145, anchor=tk.NW, window=ip_label)
canvas.create_window(345, 185, anchor=tk.NW, window=ip_entry)
canvas.create_window(522, 182, anchor=tk.NW, window=connect_button)

# Create logo label
logo_image = Image.open("config/logo_uet.png") 
logo_image = logo_image.resize((130, 130))
logo_image = ImageTk.PhotoImage(logo_image)
logo_label = tk.Label(work_frame, image=logo_image)

# Video frame display
video_label = tk.Label(work_frame)
video_label.grid(row=0, columnspan=3)

# Mode selection (Auto/Manual)
mode_label = tk.Label(work_frame, text="Mode")
mode_var = tk.StringVar(value="Auto")
mode_var.trace_add('write', switch_bs_mode)
mode_switch = ttk.Combobox(work_frame, width=6, textvariable=mode_var, values=["Auto", "Manual"], state="readonly")
mode_switch.update()

shutdown_button = tk.Button(work_frame, text=" Shutdown ", command=on_shutdown)
disconnect_button = tk.Button(work_frame, text="Disconnect", command=on_disconnect)

side_canvas = tk.Canvas(work_frame, width=320, height=480)
bottom_canvas = tk.Canvas(work_frame, width=640, height=240)

root.bind("<Left>", on_manual)
root.bind("<Right>", on_manual)
root.bind("<Up>", on_manual)
root.bind("s", on_manual)
root.bind("x", on_manual)

def show_start_sreen(is_displayed=True):
    if is_displayed:
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.focus_set()	
    else:
        canvas.pack_forget()

def show_work_screen(is_displayed=True):
    if is_displayed:
        video_label.grid(row=0, column=0, rowspan=4, columnspan=4, sticky=tk.NW)
        logo_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.NW)
  
        mode_label.grid(row=4, column=1, pady=10, sticky=tk.NW)
        mode_switch.grid(row=4, column=1, pady=35, sticky=tk.NW)

        disconnect_button.grid(row=5, column=0, padx=17, sticky=tk.NW)
        shutdown_button.grid(row=5, column=0, padx=17, pady=30, sticky=tk.SW)
  
        side_canvas.grid(row=0, column=4, rowspan=4, columnspan=2, sticky=tk.NW)
        bottom_canvas.grid(row=4, column=2, rowspan=2, columnspan=4, sticky=tk.NW)
        
        work_frame.pack(fill=tk.BOTH, expand=True)
        show_info()
        show_sensors()
        show_frame()
    else:
        shutdown_button.grid_forget()
        disconnect_button.grid_forget()
        side_canvas.grid_forget()
        work_frame.pack_forget()

def show_info():
    bottom_canvas.delete("all")
    bottom_canvas.create_text(10, 22, text=f"{bs.sys_info.vehicle_type}", font=("Arial", 16, "bold"), anchor='w')
    bottom_canvas.create_text(10, 50, text=f"Sent: {bs.sys_info.sent_msg}", anchor='w')
    bottom_canvas.create_text(10, 70, text=f"Received: {bs.sys_info.recv_msg}", font=("Arial", 11), anchor='w')

    work_frame.after(100, show_info)

def show_sensors():
    part_height = 100 / 5
    try:
        side_canvas.delete("all")
        side_canvas.create_text(75, 355, text="Distances to obstacles", font=("Arial", 11, "bold"), anchor='w')

        distances = json.loads(bs.sys_info.recv_msg)

        for i, distance in enumerate(distances):
            num_parts = min(int(distance // part_height), 4) + 1
            color = "grey"
            for j in range(5):
                if j > num_parts - 1:
                    color = "white" 
                y_start = 480 - (j + 1) * part_height
                y_end = 480 - j * part_height
                side_canvas.create_rectangle(i * 40 + 60, y_start, i * 40 + 90, y_end, fill=color)

    except Exception:
        color = "white"
        for i in range(5):
            for j in range(5):
                y_start = 480 - (j + 1) * part_height
                y_end = 480 - j * part_height
                side_canvas.create_rectangle(i * 40 + 60, y_start, i * 40 + 90, y_end, fill=color)

    work_frame.after(10, show_sensors)
 
def show_frame():
    ret, frame = bs.real_time_control()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img = ImageTk.PhotoImage(image=img)
        video_label.img = img
        video_label.config(image=img)
    else:
        img = Image.open('config/video_404.png') 
        img = ImageTk.PhotoImage(image=img)
        video_label.img = img
        video_label.config(image=img)
    video_label.after(5, show_frame)

show_start_sreen()
show_work_screen(False)

root.mainloop()
