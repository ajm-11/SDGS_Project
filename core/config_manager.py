import json
import os

class ConfigManager:
    def __init__(self, config_file="sdgs_config.json"):
        self.config_file = config_file
        self.default_config = {
            "rules": [
                {"name": "Clean Temporary Files", "ext": ".tmp", "action": "Quarantine"},
                {"name": "Archive Old Logs", "ext": ".log", "action": "Archive"}
            ],
            "monitored_folders": [],
            "protected_files": [],
            "settings": {
                "auto_scan": True,
                "scan_interval_days": 15
            }
        }
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.save_config(self.default_config)
            return self.default_config
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self.default_config

    def save_config(self, data=None):
        if data:
            self.config = data
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def get_rules(self):
        return self.config.get("rules", [])

    def add_rule(self, rule):
        self.config["rules"].append(rule)
        self.save_config()

    def remove_rule(self, rule):
        self.config["rules"] = [r for r in self.config["rules"] if r != rule]
        self.save_config()

    def get_monitored_folders(self):
        return self.config.get("monitored_folders", [])

    def add_monitored_folder(self, folder):
        if folder not in self.config["monitored_folders"]:
            self.config["monitored_folders"].append(folder)
            self.save_config()

    def remove_monitored_folder(self, folder):
        if folder in self.config["monitored_folders"]:
            self.config["monitored_folders"].remove(folder)
            self.save_config()

    def get_protected_files(self):
        return self.config.get("protected_files", [])

    def add_protected_file(self, file_path):
        if file_path not in self.config["protected_files"]:
            self.config["protected_files"].append(file_path)
            self.save_config()

    def remove_protected_file(self, file_path):
        if file_path in self.config["protected_files"]:
            self.config["protected_files"].remove(file_path)
            self.save_config()