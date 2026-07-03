# license_app/utils.py
import os
import uuid
import hashlib
import platform
import subprocess
import json, base64, datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from django.conf import settings

def get_hwid():
    # ترکیبی از MAC Address و پردازنده برای امنیت بیشتر
    mac = str(uuid.getnode())
    cpu = platform.processor()
    system = platform.system()
    
    raw_id = f"{mac}-{cpu}-{system}-Secure"
    return hashlib.sha256(raw_id.encode()).hexdigest().upper()[:24] # یک کد 24 کاراکتری




def load_publuc_key():
    try:
        public_key_path = os.path.join(settings.BASE_DIR,settings.PUBLIC_KEY_FILE )
        if os.path.exists(public_key_path):
            with open(public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())
                return public_key
        else:
            # شما می‌توانید اینجا دستوری برای خطای خروجی یا لاگ گذاشت
            print(f"خطا: فایل کلید عمومی '{public_key_path}' یافت نشد.")
            return None
    except:
        print('Error in Read public key')
        return None
    

public_key = load_publuc_key()


def validate_license(license_key: str, current_hwid: str):
    global public_key
    if public_key is None:
        public_key = load_publuc_key()
        return False, "کلید عمومی پیدا نشد. لطفاً فایل public.pem را بررسی کنید."

    # Decode license
    try:
        raw = base64.b64decode(license_key)
        payload = json.loads(raw)
    except Exception:
        return False, "فرمت لایسنس نامعتبر است"

    # Structure check
    required_fields = {"hwid", "exp", "edition", "sig"}
    if not required_fields.issubset(payload.keys()):
        return False, "ساختار لایسنس ناقص است"

    # HWID check
    if payload["hwid"] != current_hwid:
        return False, "این لایسنس برای این سیستم صادر نشده"

    # Expiry check
    try:
        exp_date = datetime.datetime.strptime(payload["exp"], "%Y-%m-%d").date()
    except ValueError:
        return False, "فرمت تاریخ انقضا نامعتبر است"

    if exp_date < datetime.date.today():
        return False, "لایسنس منقضی شده"

    # Signature check
    try:
        sig = base64.b64decode(payload["sig"])
    except Exception:
        return False, "امضای لایسنس خراب است"

    payload_copy = payload.copy()
    payload_copy.pop("sig")

    data = json.dumps(payload_copy, sort_keys=True).encode("utf-8")

    try:
        public_key.verify(
            sig,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except InvalidSignature:
        return False, "لایسنس دستکاری شده است"
    except Exception:
        return False, "خطا در بررسی لایسنس"

    return True, "OK"
