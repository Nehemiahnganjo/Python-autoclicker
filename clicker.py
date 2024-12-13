import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import pyautogui
import keyboard
import pystray
from PIL import Image, ImageGrab, ImageTk
import random
import os

class UniversalAutoclicker:
    def __init__(self):
        # Enhanced window with modern, clean theme
        self.root = tk.Tk()
        self.root.title("🖱️Nehemiah's Autoclicker Pro")
        self.root.geometry("800x750")
        self.root.configure(bg='#2C3E50')
        self.root.resizable(False, False)

        # Configurable safety settings
        pyautogui.PAUSE = 0.01
        pyautogui.FAILSAFE = True

        # Screen dimensions
        self.screen_width = pyautogui.size().width
        self.screen_height = pyautogui.size().height

        # Clicking and line drawing state
        self.lines = []
        self.current_line = None
        self.overlay = None
        self.is_clicking = False
        self.click_thread = None

        # Modes and settings variables
        self.extreme_mode = tk.BooleanVar(value=False)
        self.randomize_clicks = tk.BooleanVar(value=True)

        # Create UI components
        self.create_modern_ui()
        self.setup_hotkeys()

    def create_modern_ui(self):
        # Main container with modern styling
        main_frame = tk.Frame(self.root, bg='#2C3E50', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title with gradient effect
        title_frame = tk.Frame(main_frame, bg='#2C3E50')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(title_frame, 
                         text="🖱️ Nehemiah's Autoclicker Pro", 
                         font=('Segoe UI', 22, 'bold'), 
                         bg='#2C3E50', 
                         fg='#ECF0F1')
        title.pack()

        # Notebook for organized settings
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Clicking Settings Tab
        click_frame = ttk.Frame(notebook)
        notebook.add(click_frame, text="Click Settings")

        # Settings Grid
        settings_grid = tk.Frame(click_frame, bg='#34495E')
        settings_grid.pack(fill=tk.X, padx=10, pady=10)

        settings = [
            ("Max Clicks/Line", "9999"),
            ("Line Delay (ms)", "10"),
            ("Total Iterations", "9999"),
            ("Click Interval (ms)", "10")
        ]

        self.entries = {}
        for i, (label, default) in enumerate(settings):
            tk.Label(settings_grid, text=label, 
                     bg='#34495E', 
                     fg='#ECF0F1', 
                     font=('Segoe UI', 10)).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            
            entry = tk.Entry(settings_grid, width=20, 
                             bg='#2C3E50', 
                             fg='#ECF0F1', 
                             font=('Consolas', 10))
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=5, pady=5)
            
            self.entries[label] = entry

        # Modes Frame
        modes_frame = tk.Frame(click_frame, bg='#34495E')
        modes_frame.pack(fill=tk.X, padx=10, pady=10)

        # Extreme Mode Checkbox
        extreme_check = tk.Checkbutton(modes_frame, 
                                       text="🚨 Extreme Mode", 
                                       variable=self.extreme_mode,
                                       bg='#34495E', 
                                       fg='#E74C3C',
                                       selectcolor='#34495E')
        extreme_check.pack(side=tk.LEFT, padx=5)

        # Randomize Clicks Checkbox
        random_check = tk.Checkbutton(modes_frame, 
                                      text="🎲 Randomize Clicks", 
                                      variable=self.randomize_clicks,
                                      bg='#34495E', 
                                      fg='#3498DB',
                                      selectcolor='#34495E')
        random_check.pack(side=tk.LEFT, padx=5)

        # Control Buttons
        button_frame = tk.Frame(click_frame, bg='#34495E')
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        buttons = [
            ("Draw Line (F6)", self.start_line_drawing, '#2ECC71'),
            ("Start Clicking (F7)", self.start_clicking, '#3498DB'),
            ("Stop Clicking (F8)", self.stop_clicking, '#E74C3C'),
            ("Clear Lines", self.clear_lines, '#F39C12')
        ]

        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, 
                            command=command, 
                            bg=color, 
                            fg='white', 
                            font=('Segoe UI', 10, 'bold'))
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Lines Listbox
        lines_frame = tk.Frame(click_frame, bg='#34495E')
        lines_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(lines_frame, text="Drawn Lines:", 
                 bg='#34495E', 
                 fg='#ECF0F1', 
                 font=('Segoe UI', 10)).pack(anchor='w')

        self.line_listbox = tk.Listbox(lines_frame, 
                                       height=5, 
                                       bg='#2C3E50', 
                                       fg='#ECF0F1',
                                       selectbackground='#3498DB')
        self.line_listbox.pack(fill=tk.X)

        # Status Label
        self.status_var = tk.StringVar(value="Ready to Click")
        status_label = tk.Label(main_frame, 
                                textvariable=self.status_var, 
                                bg='#2C3E50', 
                                fg='#2ECC71',
                                font=('Segoe UI', 10))
        status_label.pack(pady=10)

    def validate_inputs(self):
        try:
            # Validate and convert inputs with reasonable defaults
            clicks_per_line = int(self.entries["Max Clicks/Line"].get())
            line_delay = max(0, float(self.entries["Line Delay (ms)"].get()) / 1000)
            iterations = max(1, int(self.entries["Total Iterations"].get()))
            click_interval = max(0, float(self.entries["Click Interval (ms)"].get()) / 1000)

            # Extreme mode overrides
            if self.extreme_mode.get():
                clicks_per_line = min(clicks_per_line * 10, 99999)
                line_delay = max(0, line_delay / 2)
                iterations = min(iterations * 10, 9999999)
                click_interval = max(0, click_interval / 2)

            return clicks_per_line, line_delay, iterations, click_interval
        except ValueError:
            messagebox.showwarning("Input Error", "Invalid numeric inputs. Using default values.")
            return 9999, 0.01, 9999, 0.01

    def start_clicking(self):
        if not self.lines:
            messagebox.showerror("Error", "Please draw at least one line first")
            return

        clicks_per_line, line_delay, iterations, click_interval = self.validate_inputs()

        self.is_clicking = True
        self.status_var.set(f"Clicking: {iterations} iterations")

        # Start clicking in a separate thread
        self.click_thread = threading.Thread(
            target=self.click_loop, 
            args=(clicks_per_line, line_delay, iterations, click_interval)
        )
        self.click_thread.daemon = True
        self.click_thread.start()

    def click_loop(self, clicks_per_line, line_delay, iterations, click_interval):
        try:
            for iteration in range(iterations):
                if not self.is_clicking:
                    return

                for line in self.lines:
                    # Generate click points
                    points = [self.calculate_click_point(line, clicks_per_line) 
                              for _ in range(clicks_per_line)]
                    
                    for point in points:
                        if not self.is_clicking:
                            return
                        
                        try:
                            pyautogui.click(point[0], point[1])
                        except Exception as e:
                            print(f"Click error: {e}")

                        time.sleep(click_interval)

                    time.sleep(line_delay)

        except Exception as e:
            print(f"Click loop error: {e}")
        finally:
            self.root.after(0, self.reset_ui)

    def calculate_click_point(self, line, max_points):
        x1, y1, x2, y2 = line
        
        if self.randomize_clicks.get():
            # Randomized point generation
            t = random.random()
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
        else:
            # More uniform distribution
            point_index = random.randint(0, max_points - 1)
            t = point_index / max_points
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
        
        return (x, y)

    def clear_lines(self):
        self.lines.clear()
        self.line_listbox.delete(0, tk.END)
        self.status_var.set("Lines cleared")

    def setup_hotkeys(self):
        keyboard.add_hotkey('f6', self.start_line_drawing)
        keyboard.add_hotkey('f7', self.start_clicking)
        keyboard.add_hotkey('f8', self.stop_clicking)

    def stop_clicking(self):
        self.is_clicking = False
        if self.click_thread:
            self.click_thread.join(timeout=1)
        self.reset_ui()

    def reset_ui(self):
        self.status_var.set("Ready to Click")
        self.is_clicking = False

    def start_line_drawing(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes('-alpha', 0.3, '-fullscreen', True, '-topmost', True)
        self.overlay.configure(bg='black')
        
        self.background = ImageGrab.grab()
        
        self.canvas = tk.Canvas(self.overlay, 
                                highlightthickness=0, 
                                cursor='cross')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        
        info_text = self.canvas.create_text(
            self.screen_width//2, 50, 
            text="Draw line: Click and drag. ESC to cancel.", 
            fill='white', 
            font=('Arial', 20)
        )
        
        self.overlay.bind('<Escape>', self.cancel_line_drawing)

    def on_press(self, event):
        self.current_line = [event.x, event.y]

    def on_drag(self, event):
        if hasattr(self, 'preview_line'):
            self.canvas.delete(self.preview_line)
        self.preview_line = self.canvas.create_line(
            self.current_line[0], self.current_line[1], 
            event.x, event.y, 
            fill='lime', width=2
        )

    def on_release(self, event):
        if self.current_line:
            line = [self.current_line[0], self.current_line[1], 
                    event.x, event.y]
            self.lines.append(line)
            
            self.line_listbox.insert(
                tk.END, 
                f"Line {len(self.lines)}: ({line[0]},{line[1]}) → ({line[2]},{line[3]})"
            )
            
            self.overlay.destroy()

    def cancel_line_drawing(self, event=None):
        if self.overlay:
            self.overlay.destroy()

    def run(self):
        self.root.mainloop()

def main():
    try:
        print("🖱️ Universal Autoclicker Pro - Starting...")
        
        # Additional safety check for dependencies
        try:
            import pyautogui
            import keyboard
            import pystray
            from PIL import Image, ImageGrab
        except ImportError as e:
            print(f"Missing dependency: {e}")
            print("Please install: pip install pyautogui keyboard pillow pystray")
            return

        app = UniversalAutoclicker()
        app.run()
    except Exception as e:
        print(f"Startup Error: {e}")

if __name__ == "__main__":
    main()
