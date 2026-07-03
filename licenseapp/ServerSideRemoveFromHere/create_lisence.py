# create_license.py
import json, base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

with open("private.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

hwid = input("HWID: ")
exp = input("Expire (YYYY-MM-DD): ")

# 1) داده‌ی قابل امضا
payload = {
    "hwid": hwid,
    "exp": exp,
    "edition": "pro",
}

# 2) ساخت رشته‌ی قابل امضا (بدون sig داخلش)
data = json.dumps(payload, sort_keys=True).encode("utf-8")

# 3) امضای RSA
signature = private_key.sign(
    data,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

# 4) اضافه کردن امضا به payload
payload["sig"] = base64.b64encode(signature).decode("ascii")

# 5) تبدیل payload کامل به یک رشته‌ی Base64 (کلید لایسنس نهایی)
license_key = base64.b64encode(
    json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
).decode("ascii")

print("\nLICENSE KEY:\n")
print(license_key)
