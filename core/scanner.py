import os
import shutil
from datetime import datetime

class DirectoryScanner:
    def __init__(self, config_manager, log_callback=None):
        self.config_mgr = config_manager
        self.log_callback = log_callback

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        if self.log_callback:
            self.log_callback(formatted_msg)
        else:
            print(formatted_msg)

    def run_scan(self):
        rules = self.config_mgr.get_rules()
        folders = self.config_mgr.get_monitored_folders()
        protected = self.config_mgr.get_protected_files()

        self.log("Starting directory governance scan...")

        if not folders:
            self.log("No monitored directories configured.")
            return

        for folder in folders:
            if not os.path.exists(folder):
                self.log(f"Warning: Monitored directory does not exist: {folder}")
                continue

            self.log(f"Scanning directory: {folder}")
            for root, _, files in os.walk(folder):
                for file_name in files:
                    file_path = os.path.join(root, file_name)

                    # التخطي إذا كان الملف محمياً
                    if file_path in protected:
                        self.log(f"Skipping protected file: {file_name}")
                        continue

                    # فحص المطابقة مع القواعد
                    for rule in rules:
                        ext = rule.get("ext", "").lower()
                        if file_name.lower().endswith(ext):
                            self.apply_action(file_path, rule)

        self.log("Scan process completed successfully.")

    def apply_action(self, file_path, rule):
        action = rule.get("action")
        rule_name = rule.get("name")

        try:
            if action == "Quarantine":
                quarantine_dir = os.path.join(os.path.dirname(file_path), ".quarantine")
                os.makedirs(quarantine_dir, exist_ok=True)
                dest = os.path.join(quarantine_dir, os.path.basename(file_path))
                shutil.move(file_path, dest)
                self.log(f"[QUARANTINE] Moved '{os.path.basename(file_path)}' per rule '{rule_name}'.")

            elif action == "Archive":
                archive_dir = os.path.join(os.path.dirname(file_path), ".archive")
                os.makedirs(archive_dir, exist_ok=True)
                dest = os.path.join(archive_dir, os.path.basename(file_path))
                shutil.move(file_path, dest)
                self.log(f"[ARCHIVE] Archived '{os.path.basename(file_path)}' per rule '{rule_name}'.")

            elif action == "Delete":
                os.remove(file_path)
                self.log(f"[DELETE] Deleted '{os.path.basename(file_path)}' per rule '{rule_name}'.")

        except Exception as e:
            self.log(f"Error executing action '{action}' on {file_path}: {str(e)}")