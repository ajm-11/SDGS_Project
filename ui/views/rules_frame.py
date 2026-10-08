import customtkinter as ctk
from tkinter import messagebox

class RulesFrame(ctk.CTkFrame):
    def __init__(self, parent, config_mgr):
        super().__init__(parent, fg_color="transparent")
        self.config_mgr = config_mgr

        self.title_label = ctk.CTkLabel(
            self, text="Lifecycle Rules & Templates", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(anchor="w", pady=(0, 15))

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(fill="x", pady=10, padx=5, ipady=10)

        self.form_title = ctk.CTkLabel(
            self.form_frame, text="Create New Governance Rule", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.form_title.pack(anchor="w", padx=15, pady=(10, 10))

        self.name_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Rule Name (e.g., Quarantine Temp Files)")
        self.name_entry.pack(fill="x", padx=15, pady=5)

        self.opts_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.opts_frame.pack(fill="x", padx=15, pady=5)

        self.ext_entry = ctk.CTkEntry(self.opts_frame, placeholder_text="Extension (e.g., .tmp, .log, .pdf)", width=250)
        self.ext_entry.pack(side="left", padx=(0, 10))

        self.action_dropdown = ctk.CTkOptionMenu(
            self.opts_frame, values=["Quarantine", "Archive", "Delete"]
        )
        self.action_dropdown.pack(side="left")

        self.btn_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=15, pady=10)

        self.add_rule_btn = ctk.CTkButton(self.btn_frame, text="+ Add Rule", command=self.add_rule)
        self.add_rule_btn.pack(side="left", padx=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Active Lifecycle Rules")
        self.list_frame.pack(fill="both", expand=True, pady=10)

        self.refresh_rules_list()

    def add_rule(self):
        name = self.name_entry.get().strip()
        ext = self.ext_entry.get().strip()
        action = self.action_dropdown.get()

        if not name or not ext:
            messagebox.showwarning("Warning", "Please fill in all rule fields.")
            return

        new_rule = {"name": name, "ext": ext if ext.startswith(".") else f".{ext}", "action": action}
        self.config_mgr.add_rule(new_rule)

        self.name_entry.delete(0, 'end')
        self.ext_entry.delete(0, 'end')
        self.refresh_rules_list()

    def remove_rule(self, rule_item):
        self.config_mgr.remove_rule(rule_item)
        self.refresh_rules_list()

    def refresh_rules_list(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        rules = self.config_mgr.get_rules()
        if not rules:
            empty_lbl = ctk.CTkLabel(self.list_frame, text="No lifecycle rules configured yet.", text_color="gray")
            empty_lbl.pack(pady=20)
            return

        for rule in rules:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=5, padx=5)

            info_text = f"Rule: {rule['name']}  |  Extension: {rule['ext']}  |  Action: {rule['action']}"
            lbl = ctk.CTkLabel(row, text=info_text, anchor="w")
            lbl.pack(side="left", padx=10, expand=True, fill="x")

            del_btn = ctk.CTkButton(
                row, text="Remove", width=80, fg_color="#C53030", hover_color="#9B2C2C",
                command=lambda r=rule: self.remove_rule(r)
            )
            del_btn.pack(side="right", padx=5, pady=5)