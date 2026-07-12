import tkinter as tk
from tkinter import ttk

root = tk.Tk(screenName="GCS-Trainer", baseName=None, className='Tk', useTk=1)
tk.Label(root, text="Welcome to GCS Trainer", font=("Helvetica", 16)).pack(pady=10)

button = tk.Button(root, text="Tasks", width=25)
button.pack()

button = tk.Button(root, text="Exit", width=25, command=root.destroy)
button.pack()
root.mainloop()