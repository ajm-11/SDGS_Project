import os
from pathlib import Path

class FileScanner:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # استثناء مجلدات الحجر الصحي والأرشيف الخاصة بالنظام افتراضياً
        home_dir = Path.home()
        self.default_exclusions = {
            str(home_dir / "SDGS_Data" / "Quarantine"),
            str(home_dir / "SDGS_Data" / "Archive")
        }

    def scan(self):
        """
        دالة الماسح: تقرأ المجلدات المراقبة من قاعدة البيانات، 
        وتعيد تكراراً (Iterable) من القواميس لكل ملف يتم إيجاده[cite: 4].
        """
        monitored_dirs = self.db_manager.get_monitored_directories()
        
        # إذا لم يتم تحديد مجلدات، لا يتم الفحص
        if not monitored_dirs:
            return []

        scanned_files = []

        for root_dir in monitored_dirs:
            root_path = Path(root_dir)
            if not root_path.exists() or not root_path.is_dir():
                continue

            # الفحص العودي باستخدام os.walk للتحكم بالروابط الرمزية والمجلدات المستثناة
            for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
                current_dir_str = str(Path(dirpath))

                # تخطي مجلدات النظام المستثناة أو مجلدات الحجر الصحي/الأرشيف
                if any(current_dir_str.startswith(exc) for exc in self.default_exclusions):
                    continue

                # حماية ضد الروابط الرمزية الحلقية (Symlink loops)
                if os.path.islink(dirpath):
                    continue

                for filename in filenames:
                    file_path = Path(dirpath) / filename

                    # تخطي الروابط الرمزية للملفات
                    if file_path.is_symlink():
                        continue

                    # تخطي ملفات السحاب المؤقتة (OneDrive / Google Drive placeholders)
                    try:
                        stat_info = file_path.stat()
                        if stat_info.st_size == 0 and getattr(stat_info, 'st_file_attributes', 0) & 0x1000: # FILE_ATTRIBUTE_OFFLINE
                            continue
                    except Exception:
                        pass

                    try:
                        # استخراج البيانات الوصفية (Metadata)
                        size_bytes = stat_info.st_size
                        size_mb = size_bytes / (1024 * 1024)
                        
                        created = stat_info.st_ctime
                        modified = stat_info.st_mtime
                        accessed = stat_info.st_atime

                        # معالجة مشكلة ويندوز في عدم تحديث تاريخ آخر وصول (last-access) بدقة
                        age_date = modified if accessed == 0 or accessed < modified else accessed

                        file_meta = {
                            "path": str(file_path.resolve()),
                            "name": filename,
                            "extension": file_path.suffix.lower(),
                            "size_mb": round(size_mb, 4),
                            "created": created,
                            "modified": modified,
                            "accessed": accessed,
                            "age_date": age_date  # مفتاح إضافي احتياطي يقرأه محرك الحوكمة مباشرة[cite: 4]
                        }
                        scanned_files.append(file_meta)
                    except Exception:
                        # تجاوز أي ملف لا يمكن قراءة خصائصه لسبب صلاحيات
                        continue

        return scanned_files

    def __call__(self):
        """اجعل الكلاس قابلاً للاستدعاء مباشرة كدالة كما يطلبه المحرك (scanner())[cite: 4]."""
        return self.scan()