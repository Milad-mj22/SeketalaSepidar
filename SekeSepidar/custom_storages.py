# custom_storages.py
import os
from django.core.files.storage import FileSystemStorage
from django.conf import settings


class UnlimitedFileSystemStorage(FileSystemStorage):
    """
    Storage سفارشی که اجازه ذخیره در هر مسیری را می‌دهد
    """
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        # اگر location داده نشد، از MEDIA_ROOT استفاده کن
        if location is None:
            location = getattr(settings, 'MEDIA_ROOT', None)
        
        if location is None:
            raise ValueError("You must provide a location for file storage")
        
        # اطمینان از وجود پوشه
        os.makedirs(location, exist_ok=True)
        
        super().__init__(location=location, base_url=base_url, *args, **kwargs)
    
    def _open(self, name, mode='rb'):
        # باز کردن فایل
        return super()._open(name, mode)
    
    def _save(self, name, content):
        # ذخیره فایل - بدون محدودیت
        return super()._save(name, content)
    
    def delete(self, name):
        # حذف فایل
        return super().delete(name)
    
    def exists(self, name):
        # بررسی وجود فایل
        return super().exists(name)