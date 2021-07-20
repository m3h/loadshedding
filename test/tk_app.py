#!/usr/bin/env python3

import tkinter as tk
import time


class App():
    def __init__(self, loadshedding_time: str, timeout: int):
        self.cancel_shutdown = True
        if timeout == 0:
            return

        self.timeout = timeout
        self.time_start = time.time()
        self.root = tk.Tk()

        greet_txt = f"Loadshedding scheduled for {loadshedding_time}"
        self.greeting = tk.Label(text=greet_txt)
        self.greeting.pack()

        self.label = tk.Label(text="")
        self.label.pack()

        self.btn_shutdown = tk.Button(
            self.root,
            text="Shutdown",
            command=self.call_shutdown
        )
        self.btn_shutdown.pack()

        self.btn_cancel = tk.Button(
            self.root, text="Cancel",
            command=self.call_cancel
        )
        self.btn_cancel.pack()

        self.update_clock()
        self.root.mainloop()

    def get_cancel_state(self):
        return self.cancel_shutdown

    def call_shutdown(self):
        print("Shutdown")
        self.cancel_shutdown = False
        self.root.destroy()

    def call_cancel(self):
        print("Cancel")
        self.cancel_shutdown = True
        self.root.destroy()

    def update_clock(self):
        time_rem = self.timeout - (time.time() - self.time_start)
        now = f"Time to shutdown: {int(time_rem)}"
        self.label.configure(text=now)

        if time_rem <= 0:
            self.cancel_shutdown = False
            self.root.destroy()
        self.root.after(1000, self.update_clock)


app = App("12 PM", 60)

print('Shutdown cancelled?', app.get_cancel_state())
