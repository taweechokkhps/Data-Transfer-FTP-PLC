import customtkinter as ctk

class LogConsole(ctk.CTkFrame):
    def __init__(self, master, height=150, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", pady=(5, 2))
        
        lbl = ctk.CTkLabel(top_bar, text="Log Console", font=ctk.CTkFont(weight="bold"))
        lbl.pack(side="left")
        
        btn_clear = ctk.CTkButton(top_bar, text="Clear", width=50, height=22, font=ctk.CTkFont(size=11), command=self.clear_logs)
        btn_clear.pack(side="right")
        
        self.textbox = ctk.CTkTextbox(self, height=height)
        self.textbox.pack(fill="x", expand=True)
        
        self.textbox.tag_config("info", foreground="#64B5F6")
        self.textbox.tag_config("success", foreground="#00E676")
        self.textbox.tag_config("error", foreground="#FF5252")
        self.textbox.tag_config("warning", foreground="#FFB74D")
        self.textbox.tag_config("switch_mode", foreground="#E040FB")

    def append_message(self, message: str, level: str = None):
        tag = None
        if level:
            tag = level.lower().replace(" ", "_")
        else:
            lower = message.lower()
            if "[switch mode]" in lower or "502" in lower or "switching to active" in lower:
                tag = "switch_mode"
            elif "[error]" in lower or "error" in lower or "fail" in lower:
                tag = "error"
            elif "[warning]" in lower or "warning" in lower:
                tag = "warning"
            elif "[success]" in lower or "success" in lower or "downloaded" in lower or "completed" in lower:
                tag = "success"
            elif "[info]" in lower:
                tag = "info"

        if tag in ["info", "success", "error", "warning", "switch_mode"]:
            self.textbox.insert("end", message + "\n", tag)
        else:
            self.textbox.insert("end", message + "\n")
        self.textbox.see("end")

    def clear_logs(self):
        self.textbox.delete("1.0", "end")
