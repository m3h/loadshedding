#!/usr/bin/env python3

import tkinter as tk

root = tk.Tk()


def button_click():
    print("Clicked button")
    root.destroy()


button = tk.Button(root, text="Quit", command=button_click).pack()

root.mainloop()

