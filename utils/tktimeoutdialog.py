#!/usr/bin/env python3

import tkinter as tk
import time


class TkTimeoutDialog():
    """
    A class that runs a Tk-based GUI window, intended for cancelling
    operations with a timeout.
    The Dialog includes a settable message to the user, seconds available
    till timeout, an affirmative button and a cancel button.

    Initializing this class is a blocking action, until the timeout is
    reached or the user makes an action.

    Args:
        affirmative (bool): True if the dialog was accepted, or if a
            timeout occurred, else False.
        reason (str): The reason for the affirmative value (i.e. which action
            caused the affirmative action to be in its current state).
        dialog_msg (str): The message text that is presented to the user in the
            dialog.
        timeout (float): The time till automatic timeout, from when the class
            is instantiated, in seconds. This is not guaranteed to be accurate,
            and will be less precise than 1 second.
        affirmative_txt (str): The text to be displayed on the affirmative
            action button. E.g. 'Shutdown!' or 'Reboot!'.
            time_start (float): Time (seconds since the Epoch) at which
            TkTimeoutDialog object was created.
        root (tk.Tk): The root tk object for the GUI Dialog. This is the
            toplevel widget.

    Methods:
        get_affirmative():
            Get the result of the dialog or timeout, and the reason for it.

        show_notification(self, dialog_msg: str, timeout: float,
                          affirmative_txt: str,
                          timeout_update_interval: int = 1000):
            Blocking function that shows a notification to the user and
            gets input.
    """
    def __init__(self):
        self.affirmative = True
        self.reason = "__init__"

    def show_notification(self, dialog_msg: str, timeout: float = 120,
                          affirmative_txt: str = 'OK',
                          timeout_update_interval: int = 1000):
        """Shows a notification to the user, and either gets user input or
        times out.

        The user can either 'affirm' the action by pressing the
        button with the affirmative_txt, cancel the action, or let the
        notification time-out.
        Pressing the affirmative button, or letting it time-out results in
        True being returned as affirmative. Pressing the cancel button or
        closing the window results in False being returned as affirmative.

        Args:
            dialog_msg (str): The text to show in the notification pop-up.
                timeout (float, optional): Seconds after calling
                show_notification after which the dialog times-out (default is
                120 seconds).
            affirmative_txt (str, optional): The text to display on the 'affirm
                action (default is 'OK').
            timeout_update_interval (int, optional): Seconds interval between
                GUI updates of the timeout time displayed.

        Returns:
            [bool, str]: A bool indicating if the user cancelled or affirmed
                the action (possibly via a timeout). The str contains the
                reason for the bool.
        """

        self.affirmative = True
        self.reason = "Dialog Termination"

        self.dialog_msg = dialog_msg
        self.timeout = timeout
        self.affirmative_txt = affirmative_txt
        self.timeout_update_interval = timeout_update_interval

        if timeout <= 0.0:
            self.reason = "zero-valued timeout"
            return self.get_affirmative()

        self.time_start = time.time()
        self.root = tk.Tk(className=self.dialog_msg)

        self.greeting = tk.Label(text=self.dialog_msg)
        self.greeting.pack()

        self.label = tk.Label(text="")
        self.label.pack()

        self.btn_affirmative = tk.Button(
            self.root,
            text=self.affirmative_txt,
            command=self.btn_affirmative_callback
        )
        self.btn_affirmative.pack()

        self.btn_cancel = tk.Button(
            self.root,
            text="Cancel",
            command=self.btn_cancel_callback
        )
        self.btn_cancel.pack()

        self.update_clock()
        # This blocks until user input or notification timeout
        self.root.mainloop()

        return self.get_affirmative()

    def get_affirmative(self):
        """Get selected dialog-option and reason therefore

        Returns
        -------
        bool, str
            A bool indicating if the user cancelled or affirmed the action
            (possibly via a timeout). The str contains the reason for the bool.
        """

        return self.affirmative, self.reason

    def terminate_dialog(self, affirmative, reason):
        """Set affirmative and reason, and close dialog

        Args:
        affirmative (bool): If the dialog was affirmed or cancelled
        reason (str): The reason for the affirmative's value
        """

        self.affirmative = affirmative
        self.reason = reason
        self.root.destroy()

    def btn_affirmative_callback(self):
        """Callback for the affirmative button click"""

        self.terminate_dialog(True, "btn_affirmative_callback")

    def btn_cancel_callback(self):
        """Callback for the cancel button click"""

        self.terminate_dialog(False, "btn_cancel_callback")

    def update_clock(self):
        """Callback for timeout function.

        Updates time to timeout in notification, and checks if notification hs
        timed out.
        """

        time_rem = self.timeout - (time.time() - self.time_start)
        time_rem_len = len(str(int(self.timeout)))
        now_fmt = "Time to {{}}: {{:0{}}} s".format(time_rem_len)
        now = now_fmt.format(self.affirmative_txt, int(time_rem))
        self.label.configure(text=now)

        if time_rem <= 0:
            self.terminate_dialog(True, "timeout")
        # Schedule this function to be called again after
        # self.timeout_update_interval ms
        self.root.after(self.timeout_update_interval, self.update_clock)


if __name__ == "__main__":
    app = TkTimeoutDialog()
    print('Affirmative?',
          app.show_notification("Notification text here!", 15, 'Press me!'))
