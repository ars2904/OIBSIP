import tkinter as tk
import os
import sys

# Ensure local source directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.gui import VoiceAssistantGUI

def main():
    root = tk.Tk()
    
    # Custom window styling
    root.configure(bg="#0f172a")
    
    # Center window on screen
    window_width = 850
    window_height = 650
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Initialize the GUI application
    app = VoiceAssistantGUI(root)
    
    # Start the event loop
    root.mainloop()

if __name__ == "__main__":
    main()
