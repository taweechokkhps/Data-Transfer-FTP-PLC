import tkinter as tk

class ToolTip:
    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tw = None
        self._after_id = None
        self.widget.bind("<Enter>", self._schedule, add="+")
        self.widget.bind("<Leave>", self._cancel, add="+")

    def _schedule(self, event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self, event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self.tw:
            self.tw.destroy()
            self.tw = None

    def _show(self):
        if self.tw:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        self.tw.attributes("-topmost", True)
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#333333", foreground="white", relief='solid', borderwidth=1,
                         font=("Arial", "10", "normal"))
        label.pack(ipadx=4, ipady=2)

