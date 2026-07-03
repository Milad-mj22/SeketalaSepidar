import json

from django.shortcuts import render

# Create your views here.
# license_app/views.py
from django.shortcuts import render, redirect
from .utils import get_hwid, validate_license
from django.conf import settings
import os

def activate_license(request):
    hwid = get_hwid()
    error_message = None
    status = request.GET.get('status')
    error_message = request.GET.get('message','')
    if error_message =='':
        if status == 'missing':
            error_message += "نرم‌افزار فعال نیست. لطفا لایسنس تهیه کنید."
        elif status == 'invalid':
            error_message += "لایسنس نامعتبر یا منقضی شده است."

    if request.method == "POST":

        license_key = request.POST.get("license_key")

        if not license_key:
            return render(request, "license_activate.html", {
                "error_message": "کد لایسنس وارد نشده"
            })


        valid, message = validate_license(license_key, hwid)

        if valid:
            with open(settings.LICENSE_FILE, "w") as f:
                f.write(license_key)

            return redirect("/")

        return render(request, "license/license_activate.html", {
            'hwid': hwid,
            "error_message": message
        })
    return render(request, 'license/license_activate.html', {
        'hwid': hwid,
        'error_message': error_message
    })


import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def get_online_license(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "invalid method"})

    body = json.loads(request.body)
    hwid = body.get("hwid")

    if not hwid:
        return JsonResponse({"status": "error", "message": "missing hwid"})

    # این URL همان سرور فروشنده است
    VENDOR_URL = "https://vendor.com/api/get-license/"

    try:
        r = requests.post(VENDOR_URL, json={"hwid": hwid})
        vendor_data = r.json()
    except Exception as e:
        return JsonResponse({"status": "error", "message": "vendor unreachable"})

    if vendor_data.get("status") == "valid" and vendor_data.get("license_key"):
        return JsonResponse({
            "status": "success",
            "license_key": vendor_data["license_key"]
        })
    else:
        return JsonResponse({
            "status": "error",
            "message": vendor_data.get("message", "invalid response")
        })


@csrf_exempt
def verify_license_api(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "invalid method"})

    body = json.loads(request.body)
    
    license_key = body.get("license_key")
    hwid = body.get("hwid")

    # اینجا اعتبارسنجی RSA، تاریخ انقضا و HWID را انجام بده
    if validate_license(license_key, hwid):
        return JsonResponse({"status": "valid"})

    return JsonResponse({"status": "invalid", "message": "license mismatch"})
