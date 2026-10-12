import customtkinter as ctk
from tkinter import messagebox, filedialog
from database import DatabaseManager
from scanner import FileScanner
from governance_engine import GovernanceEngine

class SDGSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart Directory Governance System (SDGS)")
        self.geometry("1000 = 650" if False else "1050x680")
        
        # تهيئة النظام والربط بين المكونات
        self.db = DatabaseManager()
        self.scanner = FileScanner(self.db)
        self.engine = GovernanceEngine(self.db, self.scanner)

        # إعداد المظهر العام
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # التقسيم الرئيسي (Sidebar + Main Content)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_frames()

        # بدء المجدد الخلفي للفحص التلقائي
        self.engine.start_scheduler()

        # إيقاف المجدد بشكل آمن عند إغلاق النافذة
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="SDGS Dashboard", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # أزرار التنقل بين الشاشات
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard & Logs", command=lambda: self.show_frame("dashboard"))
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_rules = ctk.CTkButton(self.sidebar_frame, text="Lifecycle Rules", command=lambda: self.show_frame("rules"))
        self.btn_rules.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_folders = ctk.CTkButton(self.sidebar_frame, text="Monitored Folders", command=lambda: self.show_frame("folders"))
        self.btn_folders.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_protection = ctk.CTkButton(self.sidebar_frame, text="Protected Files", command=lambda: self.show_frame("protection"))
        self.btn_protection.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", command=lambda: self.show_frame("settings"))
        self.btn_settings.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

    def setup_frames(self):
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content.grid_rowconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        # إنشاء الشاشات المختلفة
        self.frames["dashboard"] = DashboardView(self.main_content, self.engine, self.db)
        self.frames["rules"] = RulesView(self.main_content, self.db)
        self.frames["folders"] = FoldersView(self.main_content, self.db)
        self.frames["protection"] = ProtectionView(self.main_content, self.db)
        self.frames["settings"] = SettingsView(self.main_content, self.db)

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("dashboard")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, "refresh_data"):
            frame.refresh_data()

    def on_close(self):
        self.engine.stop_scheduler()
        self.destroy()


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, engine, db):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        self.db = db

        self.title = ctk.CTkLabel(self, text="System Dashboard & Logs", font=ctk.CTkFont(size=22, weight="bold"))
        self.title.pack(anchor="w", pady=(0, 15))

        # زر تشغيل الفحص اليدوي
        self.scan_btn = ctk.CTkButton(
            self, text="Start Manual Scan Now", fg_color="#2B8A3E", hover_color="#217A32",
            font=ctk.CTkFont(size=15, weight="bold"), command=self.trigger_scan
        )
        self.scan_btn.pack(anchor="w", pady=(0, 15), ipady=5)

        self.logs_label = ctk.CTkLabel(self, text="Recent Activity Logs:", font=ctk.CTkFont(size=16, weight="bold"))
        self.logs_label.pack(anchor="w", pady=(10, 5))

        # صندوق عرض السجلات
        self.logs_textbox = ctk.CTkTextbox(self, width=750, height=400, font=ctk.CTkFont(family="Consolas", size=12))
        self.logs_textbox.pack(fill="both", expand=True)

        self.refresh_data()

    def trigger_scan(self):
        # استدعاء الفحص غير المتزامن ومعالجة النتيجة عبر root.after لتجنب مشاكل الـ Threads
        success = self.engine.run_scan_async(trigger="manual", on_done=self.on_scan_complete)
        if not success:
            messagebox.showwarning("Warning", "A scan is already in progress!")
        else:
            messagebox.showinfo("Started", "Manual scan started in the background.")

    def on_scan_complete(self, stats):
        self.after(0, lambda: self._handle_scan_result(stats))

    def _handle_scan_result(self, stats):
        self.refresh_data()
        if stats.get("status") == "error":
            messagebox.showerror("Scan Error", f"Scan failed due to: {stats.get('error', 'Unknown')}")
        else:
            msg = (f"Scan Finished Successfully!\n\n"
                   f"Scanned: {stats['scanned']}\n"
                   f"Quarantined: {stats['quarantined']}\n"
                   f"Archived: {stats['archived']}\n"
                   f"Protected Skipped: {stats['protected']}\n"
                   f"Errors: {stats['errors']}")
            messagebox.showinfo("Scan Results", msg)

    def refresh_data(self):
        self.logs_textbox.delete("1.0", "end")
        logs = self.db.get_logs()
        for log in logs:
            line = f"[{log['timestamp']}] ACTION: {log['action_taken']} | FILE: {log['file_name']} | PATH: {log['original_path']}\n"
            self.logs_textbox.insert("end", line)


class RulesView(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db

        self.title = ctk.CTkLabel(self, text="Lifecycle Rules Configuration", font=ctk.CTkFont(size=22, weight="bold"))
        self.title.pack(anchor="w", pady=(0, 15))

        # نموذج إضافة قاعدة
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(fill="x", pady=10, padx=5, ipady=10)

        ctk.CTkLabel(self.form_frame, text="Rule Name:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(self.form_frame, width=150)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(self.form_frame, text="Extension (.ext):").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.ext_entry = ctk.CTkEntry(self.form_frame, width=100)
        self.ext_entry.insert(0, ".txt")
        self.ext_entry.grid(row=0, column=3, padx=10, pady=10)

        ctk.CTkLabel(self.form_frame, text="Action:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.action_var = ctk.StringVar(value="Quarantine")
        self.action_menu = ctk.CTkOptionMenu(self.form_frame, variable=self.action_var, values=["Quarantine", "Archive", "Delete"])
        self.action_menu.grid(row=1, column=1, padx=10, pady=10)

        self.add_btn = ctk.CTkButton(self.form_frame, text="Add Rule", command=self.add_rule)
        self.add_btn.grid(row=1, column=3, padx=10, pady=10)

        self.rules_label = ctk.CTkLabel(self, text="Existing Rules:", font=ctk.CTkFont(size=16, weight="bold"))
        self.rules_label.pack(anchor="w", pady=(15, 5))

        self.rules_textbox = ctk.CTkTextbox(self, width=750, height=300)
        self.rules_textbox.pack(fill="both", expand=True)

        self.refresh_data()

    def add_rule(self):
        name = self.name_entry.get().strip()
        ext = self.ext_entry.get().strip()
        action = self.action_var.get()

        if not name or not ext:
            messagebox.showerror("Error", "Please fill in all rule fields.")
            return

        self.db.insert_rule(name=name, extension=ext, action=action)
        messagebox.showinfo("Success", "Rule added successfully!")
        self.refresh_data()

    def refresh_data(self):
        self.rules_textbox.delete("1.0", "end")
        rules = self.db.get_all_rules()
        for r in rules:
            line = f"ID: {r['rule_id']} | Name: {r['name']} | Ext: {r['extension']} | Action: {r['action']} | Priority: {r.get('priority', 1)}\n"
            self.rules_textbox.insert("end", line)


class FoldersView(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db

        self.title = ctk.CTkLabel(self, text="Monitored Directories Management", font=ctk.CTkFont(size=22, weight="bold"))
        self.title.pack(anchor="w", pady=(0, 15))

        self.btn_browse = ctk.CTkButton(self, text="Browse & Add Folder", command=self.browse_folder)
        self.btn_browse.pack(anchor="w", pady=10)

        self.folders_label = ctk.CTkLabel(self, text="Currently Watched Folders:", font=ctk.CTkFont(size=16, weight="bold"))
        self.folders_label.pack(anchor="w", pady=(15, 5))

        self.folders_textbox = ctk.CTkTextbox(self, width=750, height=350)
        self.folders_textbox.pack(fill="both", expand=True)

        self.refresh_data()

    def browse_folder(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.db.add_monitored_directory(dir_path)
            messagebox.showinfo("Success", f"Directory added: {dir_path}")
            self.refresh_data()

    def refresh_data(self):
        self.folders_textbox.delete("1.0", "end")
        folders = self.db.get_monitored_directories()
        for f in folders:
            self.folders_textbox.insert("end", f"{f}\n")


class ProtectionView(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db

        self.title = ctk.CTkLabel(self, text="Protected Files Management", font=ctk.CTkFont(size=22, weight="bold"))
        self.title.pack(anchor="w", pady=(0, 15))

        self.btn_add = ctk.CTkButton(self, text="Select File to Protect", command=self.select_file)
        self.btn_add.pack(anchor="w", pady=10)

        self.prot_label = ctk.CTkLabel(self, text="Protected Files List:", font=ctk.CTkFont(size=16, weight="bold"))
        self.prot_label.pack(anchor="w", pady=(15, 5))

        self.prot_textbox = ctk.CTkTextbox(self, width=750, height=350)
        self.prot_textbox.pack(fill="both", expand=True)

        self.refresh_data()

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.db.add_protected_file(file_path)
            messagebox.showinfo("Success", f"File protected: {file_path}")
            self.refresh_data()

    def refresh_data(self):
        self.prot_textbox.delete("1.0", "end")
        files = self.db.get_protected_files()
        for f in files:
            self.prot_textbox.insert("end", f"{f}\n")


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db

        self.title = ctk.CTkLabel(self, text="System Settings", font=ctk.CTkFont(size=22, weight="bold"))
        self.title.pack(anchor="w", pady=(0, 20))

        self.scan_group = ctk.CTkFrame(self)
        self.scan_group.pack(fill="x", pady=10, padx=5, ipady=10)

        # قراءة الإعدادات الحالية من قاعدة البيانات
        current_mode = self.db.get_setting("scan_mode") or "manual"
        interval_str = self.db.get_setting("scan_interval_days")
        retention_str = self.db.get_setting("quarantine_retention_days")

        self.auto_scan_var = ctk.BooleanVar(value=(current_mode == "auto"))
        self.auto_scan_switch = ctk.CTkSwitch(
            self.scan_group, text="Enable Automatic Background Scanning (Auto Mode)", variable=self.auto_scan_var
        )
        self.auto_scan_switch.pack(anchor="w", padx=15, pady=15)

        # فترة الفحص بالأيام
        self.interval_frame = ctk.CTkFrame(self.scan_group, fg_color="transparent")
        self.interval_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(self.interval_frame, text="Scan Interval (Days):").pack(side="left", padx=(0, 10))
        self.interval_entry = ctk.CTkEntry(self.interval_frame, width=100)
        self.interval_entry.insert(0, interval_str if interval_str else "15")
        self.interval_entry.pack(side="left")

        # فترة الحجر الصحي بالأيام
        self.retention_frame = ctk.CTkFrame(self.scan_group, fg_color="transparent")
        self.retention_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(self.retention_frame, text="Quarantine Retention (Days):").pack(side="left", padx=(0, 10))
        self.retention_entry = ctk.CTkEntry(self.retention_frame, width=100)
        self.retention_entry.insert(0, retention_str if retention_str else "15")
        self.retention_entry.pack(side="left")

        self.save_btn = ctk.CTkButton(
            self, text="Save Settings", fg_color="#2B8A3E", hover_color="#217A32", command=self.save_settings
        )
        self.save_btn.pack(anchor="e", pady=20, padx=5)

    def save_settings(self):
        try:
            interval_days = int(self.interval_entry.get().strip())
            retention_days = int(self.retention_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for days.")
            return

        mode = "auto" if self.auto_scan_var.get() else "manual"

        self.db.set_setting("scan_mode", mode)
        self.db.set_setting("scan_interval_days", interval_days)
        self.db.set_setting("quarantine_retention_days", retention_days)

        messagebox.showinfo("Success", "Settings saved successfully!")

    def refresh_data(self):
        pass