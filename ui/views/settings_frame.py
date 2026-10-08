import customtkinter as ctk

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.title_label = ctk.CTkLabel(
            self, text="System Settings", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(anchor="w", pady=(0, 20))

        self.scan_group = ctk.CTkFrame(self)
        self.scan_group.pack(fill="x", pady=10, padx=5, ipady=10)

        self.scan_title = ctk.CTkLabel(
            self.scan_group, text="Scanning Configuration", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.scan_title.pack(anchor="w", padx=15, pady=(10, 5))

        self.auto_scan_var = ctk.BooleanVar(value=True)
        self.auto_scan_switch = ctk.CTkSwitch(
            self.scan_group, text="Enable Automatic Background Scanning", variable=self.auto_scan_var
        )
        self.auto_scan_switch.pack(anchor="w", padx=15, pady=10)

        self.interval_frame = ctk.CTkFrame(self.scan_group, fg_color="transparent")
        self.interval_frame.pack(fill="x", padx=15, pady=5)

        self.interval_label = ctk.CTkLabel(self.interval_frame, text="Scan Interval (Days):")
        self.interval_label.pack(side="left", padx=(0, 10))

        self.interval_entry = ctk.CTkEntry(self.interval_frame, width=100)
        self.interval_entry.insert(0, "15")
        self.interval_entry.pack(side="left")

        self.save_btn = ctk.CTkButton(self, text="Save Settings", fg_color="#2B8A3E", hover_color="#217A32")
        self.save_btn.pack(anchor="e", pady=20, padx=5)