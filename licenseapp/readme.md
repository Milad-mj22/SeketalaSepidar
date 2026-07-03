
جمع‌آوری HWID سمت کلاینت
تولید لایسنس امضاشده با RSA سمت سرور
اعتبارسنجی محلی امضا، HWID و تاریخ انقضا
پشتیبانی از فعال‌سازی آفلاین/آنلاین


معماری

Vendor/Server:
نگهداری private.pem
ساخت payload و امضای RSA
صدور license_key
Client/Product (Django):
شامل public.pem
نمایش HWID، دریافت license_key
verify امضا + بررسی HWID/exp
اجرای Middleware برای کنترل دسترسی


############ SETUP ##################

1- First app in Project and install app
2- add app name in settings.py
3- add app name in urls.py with name license
4- add 'licenseapp.middleware.LicenseCheckMiddleware' in MIDDLEWARE in settings.py
5- add LICENSE_FILE = 'license.key' in settings.py
6- move folder ServerSideRemoveFromHere to Where you want out of product


############ Create License ##########
1- run geneearte_keys.py , give 2 file private and public
2- create license with create_license.py
3- copy hwid from webpage and paste and then copy license from terminal in webpage