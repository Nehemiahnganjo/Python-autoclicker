import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog
import pyautogui
import keyboard
import pystray
from PIL import Image, ImageTk
import os

class AdvancedAutoclicker:
    def __init__(self):
        # Main window setup
        self.root = tk.Tk()
        self.root.title("Advanced Multipoint Autoclicker")
        self.root.geometry("600x700")
        self.root.configure(bg='#f4f4f4')

        # State variables
        self.click_points = []
        self.is_clicking = False
        self.click_thread = None
        
        # Create UI components
        self.create_ui()
        
        # Systray setup
        self.setup_systray()

    def create_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg='#f4f4f4')
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(main_frame, text="Advanced Multipoint Autoclicker", 
                                font=('Helvetica', 16, 'bold'), bg='#f4f4f4')
        title_label.pack(pady=(0, 20))

        # Points Frame
        points_frame = tk.LabelFrame(main_frame, text="Click Points", bg='#f4f4f4')
        points_frame.pack(fill=tk.X, pady=10)

        # Point List with Scrollbar
        self.point_listbox = tk.Listbox(points_frame, height=10, width=70)
        self.point_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(points_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.point_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.point_listbox.yview)

        # Buttons Frame
        buttons_frame = tk.Frame(main_frame, bg='#f4f4f4')
        buttons_frame.pack(fill=tk.X, pady=10)

        # Record Points Button
        record_btn = tk.Button(buttons_frame, text="Record Points (F6)", command=self.start_recording, 
                               bg='#4CAF50', fg='white')
        record_btn.pack(side=tk.LEFT, padx=5)

        # Remove Point Button
        remove_btn = tk.Button(buttons_frame, text="Remove Selected Point", command=self.remove_point, 
                               bg='#f44336', fg='white')
        remove_btn.pack(side=tk.LEFT, padx=5)

        # Clear Points Button
        clear_btn = tk.Button(buttons_frame, text="Clear All Points", command=self.clear_points, 
                              bg='#ff9800', fg='white')
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Settings Frame
        settings_frame = tk.LabelFrame(main_frame, text="Clicking Settings", bg='#f4f4f4')
        settings_frame.pack(fill=tk.X, pady=10)

        # Clicks per Point
        tk.Label(settings_frame, text="Clicks per Point:", bg='#f4f4f4').grid(row=0, column=0, padx=5, pady=5)
        self.clicks_entry = tk.Entry(settings_frame, width=10)
        self.clicks_entry.insert(0, "1")
        self.clicks_entry.grid(row=0, column=1, padx=5, pady=5)

        # Delay Between Points
        tk.Label(settings_frame, text="Delay Between Points (s):", bg='#f4f4f4').grid(row=0, column=2, padx=5, pady=5)
        self.delay_entry = tk.Entry(settings_frame, width=10)
        self.delay_entry.insert(0, "0.5")
        self.delay_entry.grid(row=0, column=3, padx=5, pady=5)

        # Iterations
        tk.Label(settings_frame, text="Total Iterations:", bg='#f4f4f4').grid(row=1, column=0, padx=5, pady=5)
        self.iterations_entry = tk.Entry(settings_frame, width=10)
        self.iterations_entry.insert(0, "1")
        self.iterations_entry.grid(row=1, column=1, padx=5, pady=5)

        # Start/Stop Buttons Frame
        control_frame = tk.Frame(main_frame, bg='#f4f4f4')
        control_frame.pack(fill=tk.X, pady=10)

        # Start Button
        self.start_btn = tk.Button(control_frame, text="Start Clicking (F7)", command=self.start_clicking, 
                                   bg='#2196F3', fg='white')
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Stop Button
        self.stop_btn = tk.Button(control_frame, text="Stop Clicking (F8)", command=self.stop_clicking, 
                                  bg='#f44336', fg='white', state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Status Label
        self.status_label = tk.Label(main_frame, text="Ready", bg='#f4f4f4', font=('Helvetica', 10))
        self.status_label.pack(pady=10)

        # Hotkey setup
        keyboard.add_hotkey('f6', self.start_recording)
        keyboard.add_hotkey('f7', self.start_clicking)
        keyboard.add_hotkey('f8', self.stop_clicking)

    def setup_systray(self):
        # Create system tray icon
        icon_path = self.create_tray_icon()
        image = Image.open(icon_path)
        
        def on_quit(icon):
            icon.stop()
            self.root.quit()
            sys.exit(0)

        import pystray
        menu = (
            pystray.MenuItem('Show', self.show_window),
            pystray.MenuItem('Quit', on_quit)
        )
        self.icon = pystray.Icon("Autoclicker", image, "Autoclicker", menu)

    def create_tray_icon(self):
        # Create a simple icon for system tray
        icon = Image.new('RGB', (64, 64), color='#2196F3')
        icon_path = 'autoclicker_icon.png'
        icon.save(icon_path)
        return icon_path

    def show_window(self, icon=None):
        # Show the main window and stop the system tray
        if icon:
            icon.stop()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def start_recording(self):
        # Hide main window
        self.root.withdraw()
        
        # Create transparent overlay for recording
        overlay = tk.Toplevel(self.root)
        overlay.attributes('-alpha', 0.3, '-fullscreen', True, '-topmost', True)
        overlay.configure(bg='gray')
        
        # Label for instructions
        label = tk.Label(overlay, text="Click to record points. Press ESC to finish.", 
                         font=('Helvetica', 16), bg='white')
        label.pack(expand=True)
        
        def on_click(event):
            # Record point
            point = (event.x, event.y)
            self.click_points.append(point)
            self.point_listbox.insert(tk.END, f"Point {len(self.click_points)}: ({point[0]}, {point[1]})")
        
        def on_esc(event):
            # Finish recording
            overlay.destroy()
            self.root.deiconify()
        
        # Bind events
        overlay.bind('<Button-1>', on_click)
        overlay.bind('<Escape>', on_esc)
        overlay.focus_set()

    def remove_point(self):
        # Remove selected point from listbox and points list
        try:
            selected_index = self.point_listbox.curselection()[0]
            self.point_listbox.delete(selected_index)
            del self.click_points[selected_index]
        except IndexError:
            messagebox.showwarning("Warning", "No point selected to remove.")

    def clear_points(self):
        # Clear all points
        self.click_points.clear()
        self.point_listbox.delete(0, tk.END)

    def start_clicking(self):
        # Validate inputs
        try:
            clicks_per_point = int(self.clicks_entry.get())
            delay = float(self.delay_entry.get())
            iterations = int(self.iterations_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please check your settings.")
            return

        # Validate points
        if not self.click_points:
            messagebox.showerror("Error", "No points recorded. Record points first.")
            return

        # Update UI state
        self.is_clicking = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Clicking in progress...", fg='green')

        # Start clicking in a separate thread
        self.click_thread = threading.Thread(target=self.click_loop, 
                                             args=(clicks_per_point, delay, iterations))
        self.click_thread.start()

    def click_loop(self, clicks_per_point, delay, iterations):
        try:
            # Perform clicking iterations
            for _ in range(iterations):
                if not self.is_clicking:
                    break
                
                for point in self.click_points:
                    if not self.is_clicking:
                        break
                    
                    # Perform multiple clicks at each point
                    for _ in range(clicks_per_point):
                        pyautogui.click(point[0], point[1])
                    
                    # Delay between points
                    time.sleep(delay)
        except Exception as e:
            messagebox.showerror("Error", f"Clicking error: {str(e)}")
        finally:
            # Reset UI after clicking
            self.root.after(0, self.reset_ui)

    def stop_clicking(self):
        # Stop the clicking process
        self.is_clicking = False
        if self.click_thread:
            self.click_thread.join()
        self.reset_ui()

    def reset_ui(self):
        # Reset UI to initial state
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Clicking stopped.", fg='red')

    def run(self):
        # Start the systray in a separate thread
        import threading
        systray_thread = threading.Thread(target=self.icon.run)
        systray_thread.start()

        # Start the main Tkinter event loop
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        self.root.mainloop()

    def minimize_to_tray(self):
        # Minimize to system tray instead of closing
        self.root.withdraw()
        self.icon.run()

# Dependencies installation instructions
print("Please install dependencies:")
print("pip install pyautogui keyboard pystray pillow")

# Run the application
if __name__ == "__main__":
    app = AdvancedAutoclicker()
    app.run()
