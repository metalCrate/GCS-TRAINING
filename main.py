import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import csv
from tkinter import messagebox 

users_list_path = 'data/users.csv'
uids_list = []

with open(users_list_path, 'r') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        if(i == 0):  # Skip header
            continue

        uids_list.append(row[0])

print(uids_list)
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Welcome to GCS Trainer", font=default_font).pack(pady=10)
        tk.Label(self, text="Participant ID:").pack(pady=(20,5))

        self.user_var = tk.StringVar()
        self.username_entry = tk.Entry(self, width=30, textvariable=self.user_var)
        self.username_entry.pack(pady=5)

        login_btn = tk.Button(self, text="Login", width=25, command=self.do_login, state = 'disabled')
        login_btn.pack(pady=10)
        self.login_btn = login_btn

        exit_btn = tk.Button(self, text="Exit", width=25, command=self.controller.destroy)
        exit_btn.pack(pady=5)
        self.username_entry.bind("<Return>", lambda event: self.do_login())

        self.user_var.trace('w', self.on_input_change)

    def do_login(self):
        uid = self.user_var.get().strip()
        
        if uid == "":
            messagebox.showerror("Missing ID", "Please enter a Participant ID.")
            return
        
        self.controller.participant_id = uid
        self.controller.show_frame(TaskSelectionPage)

    def on_input_change(self, *args):
        uid = self.user_var.get().strip()
        valid_ids = uids_list

        if not uid:
            self.login_btn.config(text = 'Enter ID to login', state='disabled')
        elif uid in valid_ids:
            self.login_btn.config(text = 'Login', state='normal', command = self.do_login)
        else:
            self.login_btn.config(text = 'Register', state='normal', command = self.register_user)

    def register_user(self):
        messagebox.showerror("Not implemented", "Registration through the GUI is not implemented.")
    
        pass

class TaskSelectionPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Task selection", font=default_font).pack(pady=10)

        self.user_label = tk.Label(self, text="")
        self.user_label.pack(pady=5)

        tasks = [("Passive Drill", "passive_drill"), ("Early Delayed Match to Sample", "early_dmts")]

        for label, task_name in tasks:
            btn = tk.Button(
                self,
                text=label,
                width=30,
                command= lambda tn=task_name: self.start_task(tn)
                ).pack(pady=3)
            
        tk.Button(
            self, text = 'Logout',
            width = 25,
            command = self.logout
        ).pack(pady=10)

    def on_show(self):
        self.user_label.config(text=f"Participant ID: {self.controller.participant_id}")

    def start_task(self, task_name):
        self.controller.task_to_run = task_name
        self.controller.run_task()

    def logout(self):
        self.controller.participant_id = None
        self.controller.show_frame(LoginPage)

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__(screenName="GCS-Trainer", baseName=None, className='Tk', useTk=1)
        self.title("GCS Trainer")
        self.geometry("400x500")
        self.participant_id = None
        self.task_to_run = None

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for PageClass in (LoginPage, TaskSelectionPage):
            page = PageClass(parent=container, controller=self)
            self.frames[PageClass] = page
            page.grid(row=0, column=0, sticky="nsew")
        
        global default_font
        default_font = tkfont.nametofont("TkDefaultFont")
        self.show_frame(LoginPage)

    def show_frame(self, page_class):
        frame = self.frames[page_class]

        if hasattr(frame, 'on_show'):
            frame.on_show()
        
        frame.tkraise()

    def run_task(self):
        if self.task_to_run == "passive_drill":
            from src import run_passive_drill
            run_passive_drill()
        elif self.task_to_run == "early_dmts":
            from src import run_early_dmts
            run_early_dmts()
        else:
            messagebox.showerror("Error", f"Unknown task: {self.task_to_run}")

default_font = None
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
