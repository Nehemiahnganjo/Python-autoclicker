import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
import keyboard
import pystray
from PIL import Image, ImageGrab
import random
import queue

class UniversalAutoclicker:
    def __init__(self):
        # Compact window for 720p screens
        self.root = tk.Tk()
        self.root.title("Universal Clicker")
        self.root.geometry("600x500")
        self.root.configure(bg='#1a1a1a')

        # Screen dimensions
        self.screen_width = pyautogui.size().width
        self.screen_height = pyautogui.size().height

        # Line drawing state
        self.lines = []
        self.current_line = None
        self.overlay = None

        # Performance variables
        self.is_clicking = False
        self.click_thread = None

        # Create UI
        self.create_compact_ui()
        self.setup_hotkeys()

    def create_compact_ui(self):
        # Main frame with dark theme
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Compact Title
        title = tk.Label(main_frame, text="Universal Clicker", 
                         font=('Arial', 16, 'bold'), 
                         bg='#1a1a1a', 
                         fg='#00ffff')
        title.pack(pady=5)

        # Settings Frame
        settings_frame = tk.Frame(main_frame, bg='#1a1a1a')
        settings_frame.pack(fill=tk.X, pady=5)

        # Compact Settings
        settings = [
            ("Clicks/Line", "10"),
            ("Line Delay (ms)", "0"),
            ("Iterations", "1"),
            ("Click Interval (ms)", "10")
        ]

        self.entries = {}
        for i, (label, default) in enumerate(settings):
            frame = tk.Frame(settings_frame, bg='#1a1a1a')
            frame.pack(fill=tk.X, pady=2)
            
            lbl = tk.Label(frame, text=label, 
                           bg='#1a1a1a', 
                           fg='#00ffff', 
                           width=15, 
                           anchor='w')
            lbl.pack(side=tk.LEFT)
            
            entry = tk.Entry(frame, width=10, 
                             bg='#2a2a2a', 
                             fg='#00ff00')
            entry.insert(0, default)
            entry.pack(side=tk.LEFT, padx=5)
            
            self.entries[label] = entry

        # Control Buttons
        button_frame = tk.Frame(main_frame, bg='#1a1a1a')
        button_frame.pack(fill=tk.X, pady=5)

        buttons = [
            ("Draw Line (F6)", self.start_line_drawing, '#00ffff'),
            ("Start Clicking (F7)", self.start_clicking, '#00ff00'),
            ("Stop (F8)", self.stop_clicking, '#ff0066')
        ]

        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, 
                            command=command, 
                            bg=color, 
                            fg='#000000', 
                            font=('Arial', 10, 'bold'))
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Line List
        self.line_listbox = tk.Listbox(main_frame, 
                                       height=5, 
                                       bg='#2a2a2a', 
                                       fg='#00ff00')
        self.line_listbox.pack(fill=tk.X, pady=5)

        # Status Label
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(main_frame, 
                                textvariable=self.status_var, 
                                bg='#1a1a1a', 
                                fg='#00ffff')
        status_label.pack(pady=5)

    def setup_hotkeys(self):
        keyboard.add_hotkey('f6', self.start_line_drawing)
        keyboard.add_hotkey('f7', self.start_clicking)
        keyboard.add_hotkey('f8', self.stop_clicking)

    def start_line_drawing(self):
        # Create full-screen transparent overlay
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes('-alpha', 0.3, '-fullscreen', True, '-topmost', True)
        self.overlay.configure(bg='black')
        
        # Capture current screen
        self.background = ImageGrab.grab()
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(self.overlay, 
                                highlightthickness=0, 
                                cursor='cross')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind drawing events
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        
        # Instructions
        info_text = self.canvas.create_text(
            self.screen_width//2, 50, 
            text="Draw line: Click and drag. ESC to cancel.", 
            fill='white', 
            font=('Arial', 20)
        )
        
        # Bind escape key to cancel
        self.overlay.bind('<Escape>', self.cancel_line_drawing)

    def on_press(self, event):
        # Start of line drawing
        self.current_line = [event.x, event.y]

    def on_drag(self, event):
        # Draw line preview
        if hasattr(self, 'preview_line'):
            self.canvas.delete(self.preview_line)
        self.preview_line = self.canvas.create_line(
            self.current_line[0], self.current_line[1], 
            event.x, event.y, 
            fill='lime', width=2
        )

    def on_release(self, event):
        # Finalize line
        if self.current_line:
            line = [self.current_line[0], self.current_line[1], 
                    event.x, event.y]
            self.lines.append(line)
            
            # Update line listbox
            self.line_listbox.insert(
                tk.END, 
                f"Line {len(self.lines)}: ({line[0]},{line[1]}) → ({line[2]},{line[3]})"
            )
            
            # Close overlay
            self.overlay.destroy()

    def cancel_line_drawing(self, event=None):
        # Cancel line drawing
        if self.overlay:
            self.overlay.destroy()

    def calculate_random_point_on_line(self, line):
        # Generate random point on line
        x1, y1, x2, y2 = line
        t = random.random()
        x = int(x1 + t * (x2 - x1))
        y = int(y1 + t * (y2 - y1))
        return (x, y)

    def start_clicking(self):
        try:
            clicks_per_line = int(self.entries["Clicks/Line"].get())
            line_delay = float(self.entries["Line Delay (ms)"].get()) / 1000
            iterations = int(self.entries["Iterations"].get())
            click_interval = float(self.entries["Click Interval (ms)"].get()) / 1000
        except ValueError:
            messagebox.showerror("Error", "Invalid settings")
            return

        if not self.lines:
            messagebox.showerror("Error", "No lines drawn")
            return

        # Start clicking
        self.is_clicking = True
        self.status_var.set("Clicking...")

        # Start high-speed clicking thread
        self.click_thread = threading.Thread(
            target=self.click_loop, 
            args=(clicks_per_line, line_delay, iterations, click_interval)
        )
        self.click_thread.daemon = True
        self.click_thread.start()

    def click_loop(self, clicks_per_line, line_delay, iterations, click_interval):
        try:
            for _ in range(iterations):
                for line in self.lines:
                    if not self.is_clicking:
                        return

                    # Ultra-fast clicking on random line points
                    for _ in range(clicks_per_line):
                        point = self.calculate_random_point_on_line(line)
                        pyautogui.click(point[0], point[1])
                        time.sleep(click_interval)

                    time.sleep(line_delay)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Click Error", str(e)))
        finally:
            self.root.after(0, self.reset_ui)

    def stop_clicking(self):
        self.is_clicking = False
        if self.click_thread:
            self.click_thread.join(timeout=1)
        self.reset_ui()

    def reset_ui(self):
        self.status_var.set("Ready")

    def run(self):
        self.root.mainloop()

def main():
    print("Universal Clicker - Starting...")
    try:
        app = UniversalAutoclicker()
        app.run()
    except Exception as e:
        print(f"Startup Error: {e}")

if __name__ == "__main__":
    main()

# Dependency Installation
print("\nInstall dependencies:")
print("pip install pyautogui keyboard pillow")
