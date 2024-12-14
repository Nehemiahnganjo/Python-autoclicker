import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
import keyboard
import random
import logging
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('autoclicker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UniversalAutoclicker:
    def __init__(self):
        # Enhanced window with modern, clean theme
        self.root = tk.Tk()
        self.root.title("🖱️Nehemiah's Autoclicker Pro")
        self.root.geometry("700x650")
        self.root.configure(bg='#2C3E50')
        self.root.resizable(False, False)

        # Safety and error handling configurations
        pyautogui.PAUSE = 0.01
        pyautogui.FAILSAFE = True

        # Screen dimensions
        self.screen_width = pyautogui.size().width
        self.screen_height = pyautogui.size().height

        # Clicking and line drawing state
        self.lines: List[List[int]] = []
        self.current_line: Optional[List[int]] = None
        self.overlay: Optional[tk.Toplevel] = None
        self.is_clicking = False
        self.click_thread: Optional[threading.Thread] = None
        self.preview_line = None  # Explicitly initialize preview_line

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
            ("Max Clicks/Line", "99999"),
            ("Line Delay (ms)", "0"),
            ("Total Iterations", "999999"),
            ("Click Interval (ms)", "0")
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

    def validate_inputs(self) -> Tuple[int, float, int, float]:
        try:
            # Validate and convert inputs with reasonable defaults
            clicks_per_line = max(1, int(self.entries["Max Clicks/Line"].get()))
            line_delay = max(0, float(self.entries["Line Delay (ms)"].get()) / 1000)
            iterations = max(1, int(self.entries["Total Iterations"].get()))
            click_interval = max(0, float(self.entries["Click Interval (ms)"].get()) / 1000)

            # Extreme mode overrides
            if self.extreme_mode.get():
                clicks_per_line = min(clicks_per_line * 10, 99999)
                line_delay = max(0, line_delay / 2)
                iterations = min(iterations * 10, 9999999)
                click_interval = max(0, click_interval / 2)

            logger.info(f"Validated inputs: Clicks/Line={clicks_per_line}, Line Delay={line_delay}, "
                        f"Iterations={iterations}, Click Interval={click_interval}")
            return clicks_per_line, line_delay, iterations, click_interval
        except ValueError:
            logger.warning("Invalid numeric inputs. Using default values.")
            messagebox.showwarning("Input Error", "Invalid numeric inputs. Using default values.")
            return 9999, 0.01, 9999, 0.01

    def start_clicking(self):
        if not self.lines:
            messagebox.showerror("Error", "Please draw at least one line first")
            return

        try:
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

        except Exception as e:
            logger.error(f"Error starting click loop: {e}")
            messagebox.showerror("Error", f"Failed to start clicking: {e}")

    def click_loop(self, clicks_per_line: int, line_delay: float, 
                   iterations: int, click_interval: float):
        try:
            for iteration in range(iterations):
                if not self.is_clicking:
                    logger.info("Clicking stopped by user")
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
                            logger.error(f"Click error: {e}")

                        time.sleep(click_interval)

                    time.sleep(line_delay)

        except Exception as e:
            logger.error(f"Click loop error: {e}")
        finally:
            self.root.after(0, self.reset_ui)

    def calculate_click_point(self, line: List[int], max_points: int) -> Tuple[int, int]:
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
        logger.info("Lines cleared")

    def setup_hotkeys(self):
        try:
            keyboard.add_hotkey('f6', self.start_line_drawing)
            keyboard.add_hotkey('f7', self.start_clicking)
            keyboard.add_hotkey('f8', self.stop_clicking)
            logger.info("Hotkeys successfully configured")
        except Exception as e:
            logger.error(f"Error setting up hotkeys: {e}")
            messagebox.showwarning("Hotkey Warning", 
                                   "Could not set up all hotkeys. Some features may be limited.")

    def stop_clicking(self):
        self.is_clicking = False
        if self.click_thread:
            try:
                self.click_thread.join(timeout=1)
            except Exception as e:
                logger.error(f"Error stopping click thread: {e}")
        self.reset_ui()
        logger.info("Clicking stopped")

    def reset_ui(self):
        self.status_var.set("Ready to Click")
        self.is_clicking = False

    def start_line_drawing(self):
        try:
            from PIL import ImageGrab

            self.overlay = tk.Toplevel(self.root)
            self.overlay.attributes('-alpha', 0.3, '-fullscreen', True, '-topmost', True)
            self.overlay.configure(bg='black')
            
            # Use thread-safe screen capture
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
            logger.info("Line drawing started")
        except Exception as e:
            logger.error(f"Error starting line drawing: {e}")
            messagebox.showerror("Error", f"Could not start line drawing: {e}")

    def on_press(self, event):
        self.current_line = [event.x, event.y]
        self.preview_line = None  # Reset preview line

    def on_drag(self, event):
        # Check if preview_line exists before trying to delete
        if self.preview_line is not None:
            try:
                self.canvas.delete(self.preview_line)
            except tk.TclError:
                # Handle cases where the line might have already been deleted
                pass
        
        # Create new preview line
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
            logger.info(f"Line {len(self.lines)} drawn")

    def cancel_line_drawing(self, event=None):
        if self.overlay:
            self.overlay.destroy()
            logger.info("Line drawing cancelled")

    def run(self):
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            logger.critical(f"Critical error in application: {e}")

    def on_closing(self):
        """Proper cleanup when closing the application"""
        try:
            # Stop any ongoing clicking

            if self.is_clicking:
                self.stop_clicking()
            
            # Unregister all hotkeys
            keyboard.unhook_all()
            
            logger.info("Application closing")
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error during application closure: {e}")

def main():
    try:
        print("🖱️ Universal Autoclicker Pro - Starting...")
        
        # Check and install dependencies
        try:
            import pyautogui
            import keyboard
            from PIL import ImageGrab
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            print("Please install required dependencies:")
            print("pip install pyautogui keyboard pillow")
            return

        # Additional safety checks
        if not pyautogui.FAILSAFE:
            logger.warning("PyAutoGUI Failsafe is disabled. Use with caution!")

        # Run the application
        app = UniversalAutoclicker()
        app.run()

    except Exception as e:
        logger.critical(f"Startup Error: {e}")
        print(f"Critical Error: {e}")
        print("Please check the log file for more details.")

if __name__ == "__main__":
    main()
