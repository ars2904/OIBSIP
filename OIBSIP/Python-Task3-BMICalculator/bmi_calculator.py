import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import database
import matplotlib
matplotlib.use("TkAgg")  # Set Tkinter as backend for matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime

# Initialize Database
database.init_db()

class BMICalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Oasis BMI Calculator & Tracker")
        self.root.geometry("950x650")
        self.root.minsize(900, 600)
        
        # Current session state
        self.users = []
        self.active_user_id = None
        
        # Set Colors & Themes
        self.bg_main = "#0f172a"      # slate-900
        self.bg_card = "#1e293b"      # slate-800
        self.bg_input = "#0b0f19"     # dark navy
        self.border_color = "#334155"  # slate-700
        
        self.text_main = "#f8fafc"    # slate-50
        self.text_muted = "#94a3b8"   # slate-400
        
        self.color_primary = "#6366f1" # Indigo-500
        self.color_accent = "#8b5cf6"  # Violet-500
        
        # Health Category Colors
        self.color_under = "#38bdf8"  # sky-400
        self.color_normal = "#10b981" # emerald-500
        self.color_over = "#f59e0b"   # amber-500
        self.color_obese = "#ef4444"  # red-500
        
        self.configure_window()
        self.configure_styles()
        self.create_widgets()
        
        # Load user data
        self.refresh_users_list()
        
    def configure_window(self):
        self.root.configure(bg=self.bg_main)
        
        # Enable grid weights for responsive scaling
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(0, weight=1)
        
    def configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure standard colors
        self.style.configure('.',
            background=self.bg_main,
            foreground=self.text_main,
            fieldbackground=self.bg_input,
            font=('Segoe UI', 10)
        )
        
        # Custom frames
        self.style.configure('Card.TFrame',
            background=self.bg_card,
            borderwidth=1,
            relief='solid',
            bordercolor=self.border_color
        )
        
        # Custom Labels
        self.style.configure('CardHeader.TLabel',
            background=self.bg_card,
            foreground=self.text_main,
            font=('Segoe UI', 13, 'bold')
        )
        
        self.style.configure('CardBody.TLabel',
            background=self.bg_card,
            foreground=self.text_muted,
            font=('Segoe UI', 10)
        )
        
        # Primary buttons
        self.style.configure('Primary.TButton',
            background=self.color_primary,
            foreground=self.text_main,
            font=('Segoe UI', 10, 'bold'),
            borderwidth=0,
            focuscolor=self.color_accent
        )
        self.style.map('Primary.TButton',
            background=[('active', self.color_accent), ('pressed', self.color_accent)]
        )
        
        # Secondary buttons
        self.style.configure('Secondary.TButton',
            background=self.border_color,
            foreground=self.text_main,
            font=('Segoe UI', 9),
            borderwidth=0
        )
        self.style.map('Secondary.TButton',
            background=[('active', '#475569')]
        )
        
        # Combobox style
        self.style.configure('TCombobox',
            background=self.bg_input,
            foreground=self.text_main,
            fieldbackground=self.bg_input,
            arrowcolor=self.text_muted
        )
        
    def create_widgets(self):
        # ================= LEFT SIDEBAR (Inputs & Settings) =================
        self.left_panel = ttk.Frame(self.root, style='Card.TFrame', padding=20)
        self.left_panel.grid(row=0, column=0, sticky='nsew', padx=(20, 10), pady=20)
        
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        # Header
        self.title_label = ttk.Label(self.left_panel, text="OASIS BMI CALCULATOR", font=('Segoe UI', 15, 'bold'), foreground=self.color_primary)
        self.title_label.grid(row=0, column=0, sticky='w', pady=(0, 20))
        
        # Section: Profile Selection
        profile_frame = ttk.LabelFrame(self.left_panel, text="User Profile", padding=10)
        profile_frame.grid(row=1, column=0, sticky='ew', pady=(0, 20))
        profile_frame.grid_columnconfigure(0, weight=1)
        
        self.user_var = tk.StringVar()
        self.user_combobox = ttk.Combobox(profile_frame, textvariable=self.user_var, state='readonly')
        self.user_combobox.grid(row=0, column=0, sticky='ew', padx=(0, 10), pady=5)
        self.user_combobox.bind("<<ComboboxSelected>>", self.on_user_selected)
        
        self.btn_new_user = ttk.Button(profile_frame, text="Add New", style='Secondary.TButton', command=self.create_new_user)
        self.btn_new_user.grid(row=0, column=1, sticky='e', pady=5)
        
        # Section: Calculation Inputs
        input_frame = ttk.LabelFrame(self.left_panel, text="Calculations", padding=15)
        input_frame.grid(row=2, column=0, sticky='ew', pady=(0, 20))
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Weight input
        lbl_weight = ttk.Label(input_frame, text="Weight (kg):")
        lbl_weight.grid(row=0, column=0, sticky='w', pady=(5, 2))
        
        self.weight_var = tk.StringVar()
        self.ent_weight = ttk.Entry(input_frame, textvariable=self.weight_var, font=('Segoe UI', 11))
        self.ent_weight.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        # Height input
        lbl_height = ttk.Label(input_frame, text="Height (cm):")
        lbl_height.grid(row=2, column=0, sticky='w', pady=(5, 2))
        
        self.height_var = tk.StringVar()
        self.ent_height = ttk.Entry(input_frame, textvariable=self.height_var, font=('Segoe UI', 11))
        self.ent_height.grid(row=3, column=0, sticky='ew', pady=(0, 20))
        
        # Action Buttons
        self.btn_calculate = ttk.Button(self.left_panel, text="CALCULATE & SAVE", style='Primary.TButton', command=self.calculate_bmi)
        self.btn_calculate.grid(row=3, column=0, sticky='ew', pady=(0, 10), ipady=5)
        
        self.btn_clear = ttk.Button(self.left_panel, text="Clear Fields", style='Secondary.TButton', command=self.clear_fields)
        self.btn_clear.grid(row=4, column=0, sticky='ew', pady=(0, 20))
        
        # Warning label for live errors
        self.lbl_error = ttk.Label(self.left_panel, text="", foreground=self.color_obese, font=('Segoe UI', 9, 'italic'))
        self.lbl_error.grid(row=5, column=0, sticky='ew')
        
        # ================= RIGHT PANEL (Display & Charts) =================
        self.right_panel = ttk.Frame(self.root)
        self.right_panel.grid(row=0, column=1, sticky='nsew', padx=(10, 20), pady=20)
        
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=1) # Upper card for BMI display
        self.right_panel.grid_rowconfigure(1, weight=2) # Lower card for Trend chart
        
        # Upper Section: Display Card
        self.card_result = ttk.Frame(self.right_panel, style='Card.TFrame', padding=15)
        self.card_result.grid(row=0, column=0, sticky='nsew', pady=(0, 10))
        
        self.card_result.grid_columnconfigure(0, weight=1)
        self.card_result.grid_columnconfigure(1, weight=1)
        self.card_result.grid_rowconfigure(0, weight=1)
        
        # Left upper: Huge BMI number
        bmi_number_frame = ttk.Frame(self.card_result)
        bmi_number_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        self.lbl_bmi_title = ttk.Label(bmi_number_frame, text="YOUR BMI SCORE", font=('Segoe UI', 10, 'bold'), foreground=self.text_muted)
        self.lbl_bmi_title.pack(anchor='w', pady=(10, 0))
        
        self.lbl_bmi_value = ttk.Label(bmi_number_frame, text="--.-", font=('Segoe UI', 38, 'bold'), foreground=self.text_main)
        self.lbl_bmi_value.pack(anchor='w')
        
        # Right upper: Classification box
        self.class_box = tk.Canvas(self.card_result, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border_color)
        self.class_box.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
        
        self.class_header = ttk.Label(self.class_box, text="HEALTH STATUS", font=('Segoe UI', 9, 'bold'), foreground=self.text_muted, background=self.bg_card)
        self.class_header.pack(anchor='center', pady=(15, 5))
        
        self.lbl_category = ttk.Label(self.class_box, text="No Data", font=('Segoe UI', 16, 'bold'), foreground=self.text_muted, background=self.bg_card)
        self.lbl_category.pack(anchor='center', pady=5)
        
        # Lower Section: Chart Card
        self.card_chart = ttk.Frame(self.right_panel, style='Card.TFrame', padding=15)
        self.card_chart.grid(row=1, column=0, sticky='nsew', pady=(10, 0))
        
        self.card_chart.grid_columnconfigure(0, weight=1)
        self.card_chart.grid_rowconfigure(0, weight=1)
        
        # Setup Empty Plot Canvas
        self.setup_chart()
        
    def setup_chart(self):
        # Create a matplotlib figure
        self.fig = Figure(figsize=(5, 3), dpi=100, facecolor=self.bg_card)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.bg_main)
        
        # Customize ticks, spines, labels
        self.ax.spines['bottom'].set_color(self.border_color)
        self.ax.spines['top'].set_color('none')
        self.ax.spines['right'].set_color('none')
        self.ax.spines['left'].set_color(self.border_color)
        self.ax.tick_params(colors=self.text_muted, which='both', labelsize=8)
        self.ax.yaxis.label.set_color(self.text_muted)
        self.ax.xaxis.label.set_color(self.text_muted)
        self.ax.set_title("BMI Progress History", color=self.text_main, fontsize=10, fontweight='bold', pad=10)
        
        # Embed Figure inside Tkinter Frame
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.card_chart)
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
        
    def refresh_users_list(self):
        """Fetch profiles from SQLite, update combobox, and select last user."""
        try:
            self.users = database.get_users()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to retrieve user profiles:\n{e}")
            self.users = []
            
        names = [u['name'] for u in self.users]
        self.user_combobox['values'] = names
        
        if not self.users:
            # Create a default 'Guest' user if database is empty
            try:
                guest_id = database.add_user("Guest")
                if guest_id:
                    self.refresh_users_list()
                    return
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to create default Guest user profile:\n{e}")
        else:
            # Auto-select the first user
            self.user_combobox.current(0)
            self.on_user_selected(None)

    def on_user_selected(self, event):
        """Update active session ID and redraw history chart on selection change."""
        selection = self.user_var.get()
        user_info = next((u for u in self.users if u['name'] == selection), None)
        
        if user_info:
            self.active_user_id = user_info['id']
            self.lbl_error.config(text="")
            self.refresh_data_view()
            
    def create_new_user(self):
        """Open popup dialog to input a name and register profile."""
        name = simpledialog.askstring("Add User", "Enter name for new profile:", parent=self.root)
        if name:
            name = name.strip()
            if not name:
                messagebox.showwarning("Invalid Input", "Profile name cannot be empty.")
                return
                
            try:
                user_id = database.add_user(name)
                if user_id:
                    self.refresh_users_list()
                    # Select the newly created user
                    index = next(i for i, u in enumerate(self.users) if u['id'] == user_id)
                    self.user_combobox.current(index)
                    self.on_user_selected(None)
                else:
                    messagebox.showerror("Profile Exists", "A user profile with that name already exists.")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to write new user to database:\n{e}")
                
    def clear_fields(self):
        self.weight_var.set("")
        self.height_var.set("")
        self.lbl_error.config(text="")
        
    def calculate_bmi(self):
        """Validate, compute BMI, save record to database, and update UI."""
        if not self.active_user_id:
            messagebox.showwarning("No Profile", "Please select or create a user profile first.")
            return
            
        weight_str = self.weight_var.get().strip()
        height_str = self.height_var.get().strip()
        
        # Validations
        if not weight_str or not height_str:
            self.lbl_error.config(text="Error: Both Weight and Height are required.")
            return
            
        try:
            weight = float(weight_str)
            height = float(height_str)
        except ValueError:
            self.lbl_error.config(text="Error: Inputs must be positive numbers.")
            return
            
        if weight <= 0 or height <= 0:
            self.lbl_error.config(text="Error: Values must be greater than zero.")
            return
            
        if height > 300: # Assuming cm, if height > 300, it's abnormally large
            self.lbl_error.config(text="Error: Height should be in centimeters (e.g. 170).")
            return
            
        # Calculation: BMI = weight (kg) / (height (m) ^ 2)
        height_meters = height / 100.0
        bmi = weight / (height_meters ** 2)
        bmi = round(bmi, 2)
        
        # Save to database
        try:
            record_id = database.add_record(self.active_user_id, weight, height, bmi)
            if not record_id:
                raise Exception("DB query returned empty record ID.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not save your BMI record:\n{e}")
            return
            
        # Success actions
        self.refresh_data_view()
        self.clear_fields()
        
    def refresh_data_view(self):
        """Update result labels and redraw trend charts based on DB history."""
        if not self.active_user_id:
            return
            
        try:
            records = database.get_records(self.active_user_id)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not retrieve BMI logs:\n{e}")
            records = []
            
        if records:
            # Display last record values
            last_record = records[-1]
            bmi_val = last_record['bmi']
            self.lbl_bmi_value.config(text=f"{bmi_val:.2f}")
            
            # Determine health category
            category, color = self.classify_bmi(bmi_val)
            self.lbl_category.config(text=category, foreground=color)
            self.class_box.config(highlightbackground=color)
        else:
            self.lbl_bmi_value.config(text="--.-")
            self.lbl_category.config(text="No Records", foreground=self.text_muted)
            self.class_box.config(highlightbackground=self.border_color)
            
        self.draw_chart_data(records)
        
    def classify_bmi(self, bmi):
        if bmi < 18.5:
            return "UNDERWEIGHT", self.color_under
        elif 18.5 <= bmi < 25:
            return "NORMAL WEIGHT", self.color_normal
        elif 25 <= bmi < 30:
            return "OVERWEIGHT", self.color_over
        else:
            return "OBESE", self.color_obese
            
    def draw_chart_data(self, records):
        """Clear axes and redraw trend chart from database logs."""
        self.ax.clear()
        
        # Styling properties
        self.ax.set_facecolor(self.bg_main)
        self.ax.spines['bottom'].set_color(self.border_color)
        self.ax.spines['top'].set_color('none')
        self.ax.spines['right'].set_color('none')
        self.ax.spines['left'].set_color(self.border_color)
        self.ax.tick_params(colors=self.text_muted, which='both', labelsize=8)
        self.ax.yaxis.label.set_color(self.text_muted)
        self.ax.xaxis.label.set_color(self.text_muted)
        self.ax.set_ylabel("BMI Score")
        
        self.ax.set_title(
            f"BMI Progress Trend: {self.user_var.get()}",
            color=self.text_main,
            fontname='Segoe UI',
            fontsize=10,
            fontweight='bold',
            pad=10
        )
        
        if len(records) > 0:
            # Extract lists
            dates = []
            bmis = []
            for r in records:
                # Format date string 'YYYY-MM-DD HH:MM:SS' to 'MM/DD'
                try:
                    dt = datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S')
                    dates.append(dt.strftime('%m/%d'))
                except Exception:
                    dates.append(r['timestamp'][:10])
                bmis.append(r['bmi'])
                
            # Plot trends line
            self.ax.plot(dates, bmis, color=self.color_primary, marker='o', linestyle='-', linewidth=2, label="Your BMI")
            
            # Draw threshold lines
            self.ax.axhline(y=18.5, color=self.color_under, linestyle='--', linewidth=0.8, alpha=0.7)
            self.ax.axhline(y=25.0, color=self.color_over, linestyle='--', linewidth=0.8, alpha=0.7)
            self.ax.axhline(y=30.0, color=self.color_obese, linestyle='--', linewidth=0.8, alpha=0.7)
            
            # Format limits & grids
            self.ax.grid(True, color=self.border_color, linestyle=':', alpha=0.5)
            
            # Dynamically adjust y limits to cover standard bounds
            min_y = min(15.0, min(bmis) - 2)
            max_y = max(35.0, max(bmis) + 2)
            self.ax.set_ylim(min_y, max_y)
            
            # If dates list is long, reduce x-axis tick density to prevent overlapping text
            if len(dates) > 7:
                self.ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(7))
                
        else:
            # Placeholder text if no records
            self.ax.text(0.5, 0.5, "No logged BMI records.\nAdd data to view trend history.",
                         color=self.text_muted, ha='center', va='center', transform=self.ax.transAxes)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            
        self.chart_canvas.draw()

if __name__ == '__main__':
    root = tk.Tk()
    app = BMICalculatorApp(root)
    root.mainloop()
