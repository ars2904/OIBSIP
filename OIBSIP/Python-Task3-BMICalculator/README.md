# Oasis BMI Calculator & Progress Tracker

A premium, modern desktop application built in Python using **Tkinter** and **Matplotlib** to compute Body Mass Index (BMI), classify results into health categories, and track progress over time for multiple users.

## Features

- **Multi-User Profile Support**: Track BMI progress independently for different named users. Includes auto-profile setup for immediate testing.
- **Embedded Trend Visualization**: Integrates a dynamic `matplotlib` line chart showing historical values over time, complete with health threshold markers.
- **Colour-Coded Classifications**: Color-coded feedback instantly indicates category bounds (Blue for Underweight, Green for Normal, Yellow for Overweight, Red for Obese).
- **Robust Exception Handling**: Prevents database read/write failures from crashing the app and shows descriptive errors for local system issues.
- **Input Validation**: Restricts input fields to positive floating-point numbers. Rejects invalid text or negative dimensions and alerts the user with dynamic error tooltips.

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Navigate to the Project Folder
Open your terminal and navigate to the task directory:
```bash
cd OIBSIP/Python-Task3-BMICalculator
```

### Step 2: Install Dependencies
Install the required packages (Matplotlib is used for rendering trends):
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
Start the desktop application:
```bash
python bmi_calculator.py
```

---

## Technical Architecture

- **`bmi_calculator.py`**: The graphical dashboard built using themed Tkinter (`ttk`) and embedded `matplotlib` graphics. Contains input validators, error handling cards, and chart refresh listeners.
- **`database.py`**: Interacts with SQLite, defining relational schema bindings for user lists and calculations. Handles logging statements and database writing traps.
- **`bmi_history.db`**: Local SQLite database storing user profiles and calculations.
