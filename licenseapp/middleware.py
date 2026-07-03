# license_app/middleware.py
import time
import urllib.parse
from django.shortcuts import redirect
from django.conf import settings
import os
from .utils import get_hwid, validate_license

class LicenseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # لیست صفحاتی که بدون لایسنس هم باید باز شوند
        allowed_paths = ['/license/activate/', '/static/']
        
        if any(request.path.startswith(path) for path in allowed_paths):
            return self.get_response(request)

        license_path = os.path.join(settings.BASE_DIR,settings.LICENSE_FILE )
        
        # چک کردن وجود فایل لایسنس
        if not os.path.exists(license_path):
            return redirect('/license/activate/?status=missing')

        # خواندن و تایید لایسنس
        with open(license_path, 'r') as f:
            key = f.read().strip()
            hwid = get_hwid()

            is_valid, message = validate_license(key, hwid)
            
        if not is_valid:
            message_encoded = urllib.parse.quote(message)
            return redirect(f'/license/activate/?status=invalid&message={message_encoded}')
        

        return self.get_response(request)
