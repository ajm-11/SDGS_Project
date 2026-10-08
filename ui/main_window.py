import customtkinter as ctk

from core.config_manager import ConfigManager
from core.scanner import DirectoryScanner

from ui.views.rules_frame import RulesFrame
from ui.views.monitored_frame import MonitoredFrame
from ui.views.protected_frame import ProtectedFrame
from ui.views.settings_frame import SettingsFrame
from ui.views.logs_frame import LogsFrame

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart Directory Governance System")
        self.geometry("1100x680")
        self.minsize(950, 600)

        self.config_mgr = ConfigManager()
        self.scanner = DirectoryScanner(self.config_mgr)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="SDGS Governance", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.btn_rules = ctk.CTkButton(self.sidebar_frame, text="Lifecycle Rules", command=lambda: self.select_frame("rules"))
        self.btn_rules.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_monitored = ctk.CTkButton(self.sidebar_frame, text="Monitored Folders", command=lambda: self.select_frame("monitored"))
        self.btn_monitored.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_protection = ctk.CTkButton(self.sidebar_frame, text="Protected Files", command=lambda: self.select_frame("protection"))
        self.btn_protection.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_logs = ctk.CTkButton(self.sidebar_frame, text="Activity Logs", command=lambda: self.select_frame("logs"))
        self.btn_logs.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", command=lambda: self.select_frame("settings"))
        self.btn_settings.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.frames = {
            "rules": RulesFrame(self.main_content_frame, self.config_mgr),
            "monitored": MonitoredFrame(self.main_content_frame, self.config_mgr),
            "protection": ProtectedFrame(self.main_content_frame, self.config_mgr),
            "settings": SettingsFrame(self.main_content_frame),
            "logs": LogsFrame(self.main_content_frame, self.scanner)
        }

        self.select_frame("rules")

    def select_frame(self, name):
        for frame in self.frames.values():
            frame.pack_forget()

        if name in self.frames:
            self.frames[name].pack(fill="both", expand=True)