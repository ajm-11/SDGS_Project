import customtkinter as ctk
from tkinter import filedialog

class MonitoredFrame(ctk.CTkFrame):
    def __init__(self, parent, config_mgr):
        super().__init__(parent, fg_color="transparent")
        self.config_mgr = config_mgr

        self.title_label = ctk.CTkLabel(
            self, text="Monitored Directories", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(anchor="w", pady=(0, 15))

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", pady=10)

        self.add_btn = ctk.CTkButton(self.top_bar, text="+ Add Directory (Browse)", command=self.browse_directory)
        self.add_btn.pack(side="left")

        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Watched Folders List")
        self.list_frame.pack(fill="both", expand=True, pady=10)

        self.refresh_folder_list()

    def browse_directory(self):
        selected_directory = filedialog.askdirectory()
        if selected_directory:
            self.config_mgr.add_monitored_folder(selected_directory)
            self.refresh_folder_list()

    def remove_directory(self, folder_path):
        self.config_mgr.remove_monitored_folder(folder_path)
        self.refresh_folder_list()

    def refresh_folder_list(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        folders = self.config_mgr.get_monitored_folders()
        if not folders:
            empty_lbl = ctk.CTkLabel(self.list_frame, text="No monitored directories added yet.", text_color="gray")
            empty_lbl.pack(pady=20)
            return

        for path in folders:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=5, padx=5)

            lbl = ctk.CTkLabel(row, text=path, anchor="w")
            lbl.pack(side="left", padx=10, expand=True, fill="x")

            del_btn = ctk.CTkButton(
                row, text="Remove", width=80, fg_color="#C53030", hover_color="#9B2C2C",
                command=lambda p=path: self.remove_directory(p)
            )
            del_btn.pack(side="right", padx=5, pady=5)