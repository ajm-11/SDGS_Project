import os
import shutil
import time
import threading
import uuid
from pathlib import Path
from datetime import datetime, timedelta

class GovernanceEngine:
    def __init__(self, db_manager, scanner):
        self.db = db_manager
        self.scanner = scanner
        self.is_running = False
        self._stop_scheduler_flag = threading.Event()
        self.scheduler_thread = None

        # تحديد مسارات الحجر الصحي والأرشيف الافتراضية الخاصة بالنظام
        home_dir = Path.home()
        self.quarantine_dir = home_dir / "SDGS_Data" / "Quarantine"
        self.archive_dir = home_dir / "SDGS_Data" / "Archive"
        
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def run_scan_async(self, trigger="manual", on_done=None, progress_cb=None):
        """
        تشغيل الفحص بشكل غير متزامن (Background Thread) لضمان عدم تجمد الواجهة.
        يعود بـ False فوراً إذا كان هناك فحص جاري حالياً.
        """
        if self.is_running:
            return False

        self.is_running = True

        def worker():
            stats = {
                "status": "done",
                "trigger": trigger,
                "scanned": 0,
                "quarantined": 0,
                "archived": 0,
                "protected": 0,
                "ignored": 0,
                "skipped": 0,
                "reaped": 0,
                "errors": 0
            }
            try:
                # 1. تنظيف الحجر الصحي من الملفات منتهية الصلاحية أولاً
                reaped_count = self._reap_expired_quarantine()
                stats["reaped"] = reaped_count

                # 2. تشغيل الماسح لجلب الملفات
                files = self.scanner()
                rules = self.db.get_all_rules()

                # ترتيب القواعد حسب الأولوية تنازلياً
                rules = sorted(rules, key=lambda r: r.get("priority", 1), reverse=True)

                for file_info in files:
                    stats["scanned"] += 1
                    file_path_str = file_info.get("path")
                    if not file_path_str:
                        stats["skipped"] += 1
                        continue

                    file_path = Path(file_path_str)
                    
                    # التحقق مما إذا كان الملف محمياً
                    if self.db.is_file_protected(file_path_str):
                        stats["protected"] += 1
                        continue

                    if not file_path.exists():
                        stats["skipped"] += 1
                        continue

                    # مطابقة القواعد مع الملف
                    matched_rule = self._match_rule(file_info, rules)
                    if matched_rule:
                        action = matched_rule.get("action", "Ignore")
                        success = self._execute_action(file_info, action)
                        if success:
                            if action.lower() == "quarantine":
                                stats["quarantined"] += 1
                            elif action.lower() == "archive":
                                stats["archived"] += 1
                            else:
                                stats["ignored"] += 1
                        else:
                            stats["errors"] += 1
                    else:
                        stats["ignored"] += 1

                # تحديث وقت آخر فحص في الإعدادات
                self.db.set_setting("last_scan_time", datetime.now().isoformat())

            except Exception as e:
                stats["status"] = "error"
                stats["error"] = str(e)
            finally:
                self.is_running = False
                if on_done:
                    on_done(stats)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        return True

    def _match_rule(self, file_info, rules):
        ext = file_info.get("extension", "").lower()
        size_mb = file_info.get("size_mb", 0)
        
        # حساب العمر بالأيام بناءً على age_date أو التعديل
        target_time = file_info.get("age_date", file_info.get("modified", time.time()))
        age_days = (time.time() - target_time) / (24 * 3600)

        for rule in rules:
            rule_ext = rule.get("extension", "").lower()
            min_size = rule.get("min_size", 0)
            max_age = rule.get("max_age_days", 0)

            # مطابقة الامتداد (إذا كانت القاعدة تطبق على الكل أو امتداد مطابق)
            ext_match = (rule_ext == "" or rule_ext == "*" or rule_ext == ext)
            size_match = (size_mb >= min_size)
            age_match = (max_age == 0 or age_days >= max_age)

            if ext_match and size_match and age_match:
                return rule
        return None

    def _execute_action(self, file_info, action):
        file_path = Path(file_info["path"])
        filename = file_info["name"]
        action_lower = action.lower()

        try:
            if action_lower == "quarantine":
                q_id = str(uuid.uuid4())
                stored_name = f"{q_id}_{filename}"
                stored_path = self.quarantine_dir / stored_name
                shutil.move(str(file_path), str(stored_path))
                
                self.db.log_action(
                    action_taken="Quarantine",
                    file_name=filename,
                    original_path=str(file_path),
                    quarantine_id=q_id,
                    stored_path=str(stored_path)
                )
                return True

            elif action_lower == "archive":
                stored_path = self.archive_dir / f"{int(time.time())}_{filename}"
                
                shutil.move(str(file_path), str(stored_path))
                self.db.log_action(
                    action_taken="Archive",
                    file_name=filename,
                    original_path=str(file_path),
                    stored_path=str(stored_path)
                )
                return True

            elif action_lower == "delete":
                file_path.unlink()
                self.db.log_action(
                    action_taken="Delete",
                    file_name=filename,
                    original_path=str(file_path)
                )
                return True

        except Exception:
            self.db.log_action(
                action_taken=f"Error_{action}",
                file_name=filename,
                original_path=str(file_path)
            )
            return False
        return False

    def _reap_expired_quarantine(self):
        """حذف الملفات المحجورة التي تجاوزت فترة الاحتفاظ المحددة في الإعدادات."""
        retention_str = self.db.get_setting("quarantine_retention_days")
        try:
            retention_days = int(retention_str) if retention_str else 15
        except ValueError:
            retention_days = 15

        reaped_count = 0
        cutoff_time = time.time() - (retention_days * 24 * 3600)

        for item in self.quarantine_dir.iterdir():
            if item.is_file():
                if item.stat().st_mtime < cutoff_time:
                    try:
                        item.unlink()
                        reaped_count += 1
                    except Exception:
                        pass
        return reaped_count

    def start_scheduler(self):
        """بدء المجدد الخلفي للفحص التلقائي بناءً على الفترة المحددة في الإعدادات."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return

        self._stop_scheduler_flag.clear()

        def scheduler_loop():
            while not self._stop_scheduler_flag.is_set():
                try:
                    scan_mode = self.db.get_setting("scan_mode")
                    # إذا لم يتم تعيين الوضع، فالافتراضي يدوي
                    if scan_mode == "auto":
                        interval_str = self.db.get_setting("scan_interval_days")
                        interval_days = int(interval_str) if interval_str else 15
                        
                        last_scan = self.db.get_setting("last_scan_time")
                        should_scan = True
                        if last_scan:
                            last_time = datetime.fromisoformat(last_scan)
                            if datetime.now() - last_time < timedelta(days=interval_days):
                                should_scan = False

                        if should_scan and not self.is_running:
                            self.run_scan_async(trigger="auto")
                except Exception:
                    pass

                # انتظار فحص الساعات أو التحقق كل دقيقة
                for _ in range(60):
                    if self._stop_scheduler_flag.is_set():
                        break
                    time.sleep(1)

        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduler(self):
        self._stop_scheduler_flag.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)