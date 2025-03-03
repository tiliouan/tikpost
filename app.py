import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading

class ScriptManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Script Control Panel")
        
        self.scripts = {
            "Upload": "upload.py",
            "Fetch Links": "fetch_links.py",
            "Download": "download.py"
        }
        
        self.processes = {}
        
        self.create_widgets()
        
    def create_widgets(self):
        row = 0
        for name in self.scripts.keys():
            tk.Label(self.root, text=name).grid(row=row, column=0, padx=10, pady=5)
            start_btn = tk.Button(self.root, text="Start", command=lambda n=name: self.start_script(n))
            start_btn.grid(row=row, column=1, padx=5, pady=5)
            stop_btn = tk.Button(self.root, text="Stop", command=lambda n=name: self.stop_script(n))
            stop_btn.grid(row=row, column=2, padx=5, pady=5)
            row += 1
        
        self.log_display = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.log_display.grid(row=row, column=0, columnspan=3, padx=10, pady=10)
        
        tk.Button(self.root, text="Clear Logs", command=self.clear_logs).grid(row=row+1, column=0, pady=5)
        tk.Button(self.root, text="Restart All", command=self.restart_all).grid(row=row+1, column=1, pady=5)
        
    def start_script(self, name):
        if name in self.processes and self.processes[name].poll() is None:
            self.log(f"{name} is already running.")
            return
        
        script = self.scripts[name]
        self.log(f"Starting {name}...")
        process = subprocess.Popen(["python", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.processes[name] = process
        
        threading.Thread(target=self.monitor_output, args=(name, process), daemon=True).start()
    
    def stop_script(self, name):
        if name in self.processes and self.processes[name].poll() is None:
            self.processes[name].terminate()
            self.log(f"Stopped {name}.")
        else:
            self.log(f"{name} is not running.")
    
    def restart_all(self):
        self.log("Restarting all scripts...")
        for name in self.scripts.keys():
            self.stop_script(name)
            self.start_script(name)
    
    def monitor_output(self, name, process):
        for line in process.stdout:
            self.log(f"[{name}] {line.strip()}")
        for line in process.stderr:
            self.log(f"[{name} ERROR] {line.strip()}")
    
    def log(self, message):
        self.log_display.insert(tk.END, message + "\n")
        self.log_display.yview(tk.END)
    
    def clear_logs(self):
        self.log_display.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptManager(root)
    root.mainloop()
