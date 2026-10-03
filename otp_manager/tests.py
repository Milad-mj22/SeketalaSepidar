from django.test import TestCase

# Create your tests here.
import http.client
import json

conn = http.client.HTTPSConnection("api.sms.ir")

# ✅ API Key جدیدت رو اینجا بذار
API_KEY = "XDOuKkAjI8x2YHHDYDbwW3ySojBavURrnbwCzdAaPf8stXLX"

payload = json.dumps({
    "lineNumber": 30002128094276,
    "messageTexts": ["تست پیامک"],
    "mobiles": ["09135689040"],
    "senddatetime": None
})

headers = {
    'Content-Type': 'application/json',
    'Accept': 'text/plain',
    'X-API-KEY': API_KEY
}

conn.request("POST", "/v1/send/likeToLike", payload, headers)
res = conn.getresponse()
data = res.read()

print("Status Code:", res.status)
print("Response:", data.decode("utf-8"))