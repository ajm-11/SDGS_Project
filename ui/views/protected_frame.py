import customtkinter as ctk
from tkinter import filedialog

class ProtectedFrame(ctk.CTkFrame):
    def __init__(self, parent, config_mgr):
        super().__init__(parent, fg_color="transparent")
        self.config_mgr = config_mgr

        self.title_label = ctk.CTkLabel(
            self, text="Protected Files & Assets", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(anchor="w", pady=(0, 15))

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", pady=10)

        self.add_btn = ctk.CTkButton(self.top_bar, text="+ Add Protected File", command=self.browse_file)
        self.add_btn.pack(side="left")

        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Protected Files List")
        self.list_frame.pack(fill="both", expand=True, pady=10)

        self.refresh_file_list()

    def browse_file(self):
        selected_file = filedialog.askopenfilename()
        if selected_file:
            self.config_mgr.add_protected_file(selected_file)
            self.refresh_file_list()

    def remove_file(self, file_path):
        self.config_mgr.remove_protected_file(file_path)
        self.refresh_file_list()

    def refresh_file_list(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        files = self.config_mgr.get_protected_files()
        if not files:
            empty_lbl = ctk.CTkLabel(self.list_frame, text="No protected files added yet.", text_color="gray")
            empty_lbl.pack(pady=20)
            return

        for path in files:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=5, padx=5)

            lbl = ctk.CTkLabel(row, text=path, anchor="w")
            lbl.pack(side="left", padx=10, expand=True, fill="x")

            del_btn = ctk.CTkButton(
                row, text="Unprotect", width=90, fg_color="#C53030", hover_color="#9B2C2C",
                command=lambda p=path: self.remove_file(p)
            )
            del_btn.pack(side="right", padx=5, pady=5)