import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from tkinter import messagebox 
import pandas as pd
import time
users_list_path = 'data/users.csv'
uids_list = []

df = pd.read_csv(users_list_path, dtype={'user_id': str, 'user_name': str, 'join_date': str})
uids_list = df['user_id'].tolist()
user_names = df['user_name'].tolist()

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.default_font = tkfont.nametofont("TkDefaultFont")
        tk.Label(self, text="Welcome to GCS Trainer", font=self.default_font).pack(pady=10)
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
        self.controller_participant_name = df.loc[df['user_id'] == uid, 'user_name'].values[0] if uid in uids_list else "Unknown"
        self.controller.participant_name = self.controller_participant_name
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

        self.default_font = tkfont.nametofont("TkDefaultFont")
        tk.Label(self, text="Task selection", font=self.default_font).pack(pady=10)

        self.user_id_label = tk.Label(self, text="")
        self.user_id_label.pack(pady=5)
        self.user_name_label = tk.Label(self, text="")
        self.user_name_label.pack(pady=5)
        self.join_date_label = tk.Label(self, text="")
        self.join_date_label.pack(pady=5)
        self.week_label = tk.Label(self, text="")
        self.week_label.pack(pady=5)
        tasks = [
            ("Passive Drill", "passive_drill"),
            ("Early Delayed Match to Sample", "early_dmts"),
            ("Late Delayed Match to Sample", "late_dmts"),
            ("Early Span", "early_span"),
            ("Late Span", "late_span"),
            ("Advanced Span", "advanced_span"),
            ("Color to Letter Speed Test", "color-to-letter"),
            ("Letter to Color Speed Test", "letter-to-color"),
            ("N-Back", "nback")
            ]

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
        self.user_id_label.config(text=f"Participant ID: {self.controller.participant_id}")
        self.user_name_label.config(text=f"Participant Name: {self.controller.participant_name}")
        join_date = df.loc[df['user_id'] == self.controller.participant_id, 'join_date'].values[0] # type: ignore
        self.join_date_label.config(text=f"Join Date: {join_date}")
        days_elapsed = (pd.Timestamp.now() - pd.to_datetime(join_date)).days
        week_number = (days_elapsed // 7) + 1
        self.week_label.config(text=f"Week Number: {week_number}")



    def start_task(self, task_name):
        self.controller.task_to_run = task_name
        self.controller.run_task()

    def logout(self):
        self.controller.participant_id = None
        self.controller.show_frame(LoginPage)

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__(screenName="GCS-Trainer", baseName=None, className='Tk', useTk=True)
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

        match self.task_to_run:
            case "passive_drill":
                from src import run_passive_drill
                run_passive_drill()
            case "early_dmts":
                from src import run_early_dmts
                run_early_dmts(self.participant_id)
            case "late_dmts": 
                from src import run_late_dmts
                run_late_dmts(self.participant_id)
            case "early_span":
                from src import run_early_span
                run_early_span(self.participant_id)
            case "late_span":
                from src import run_late_span
                run_late_span(self.participant_id)
            case "advanced_span":
                from src import run_advanced_span
                run_advanced_span(self.participant_id)
            case "color-to-letter":
                from src import run_color_to_letter
                run_color_to_letter(self.participant_id)
            case "letter-to-color":
                from src import run_letter_to_color
                run_letter_to_color(self.participant_id)
            case "nback":
                from src import run_nback
                run_nback(self.participant_id)
            case _:
                messagebox.showerror("Error", f"Unknown task: {self.task_to_run}")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
