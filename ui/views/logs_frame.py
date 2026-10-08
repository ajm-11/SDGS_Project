import customtkinter as ctk

class LogsFrame(ctk.CTkFrame):
    def __init__(self, parent, scanner):
        super().__init__(parent, fg_color="transparent")
        self.scanner = scanner

        self.title_label = ctk.CTkLabel(
            self, text="Activity & Audit Logs", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(anchor="w", pady=(0, 15))

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", pady=(0, 10))

        self.run_scan_btn = ctk.CTkButton(
            self.top_bar, text="▶ Run Scan Now", fg_color="#1D4ED8", hover_color="#1E40AF", command=self.run_scan
        )
        self.run_scan_btn.pack(side="left")

        self.logs_textbox = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=13))
        self.logs_textbox.pack(fill="both", expand=True, pady=10)

        self.scanner.log_callback = self.append_log

    def append_log(self, message):
        self.logs_textbox.configure(state="normal")
        self.logs_textbox.insert("end", message + "\n")
        self.logs_textbox.see("end")
        self.logs_textbox.configure(state="disabled")

    def run_scan(self):
        self.scanner.run_scan()