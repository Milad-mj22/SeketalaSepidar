import json
import re

from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from authentication.models import Profile
from dashboard.models import BaseSettings
from django.contrib.auth.decorators import login_required

# Create your views here.

def get_info():
    try:
        logo = BaseSettings.get_settings().logo
        url = logo.url
        description = BaseSettings.get_settings().description
        return logo,description
    except Exception as e :
        print('Error in Authentication',e)
        return '',''


def login_page(request:HttpRequest):
    
    if not request.user.is_authenticated:
        logo ,description = get_info()

        return render(request, 'sign-in.html',{'logo':logo,'app_description':description})
    else:
        return redirect('dashboard:dashboard_page') 

def check_login(request):
    if request.method == 'POST':
        try:
            # دریافت داده‌ها
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                phone = data.get('phone')
                password = data.get('password')
            else:
                phone = request.POST.get('phone')
                password = request.POST.get('password')
            
            # اعتبارسنجی اولیه
            if not phone or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'تمام فیلد ها الزامی است '
                }, status=400)
            
            # بررسی نوع ورودی (شماره تماس یا نام کاربری)
            is_phone = bool(re.match(r'^09[0-9]{9}$', phone))
            
            # جستجوی پروفایل بر اساس نوع ورودی
            try:
                if is_phone:
                    profile = Profile.objects.select_related('user').get(user__username=phone)
                else:
                    # جستجو با نام کاربری
                    profile = Profile.objects.select_related('user').get(user__username=phone)
            except Profile.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'کاربری با این مشخصات یافت نشد'
                }, status=401)
            
            # بررسی فعال بودن اکانت
            if not profile.is_active:
                return JsonResponse({
                    'status': 'error',
                    'message': 'اکانت شما غیرفعال است'
                }, status=403)
            
            # بررسی صحت رمز عبور
            if not profile.check_password(password):
                return JsonResponse({
                    'status': 'error',
                    'message': 'شماره موبایل یا کلمه عبور اشتباه است'
                }, status=401)
            
            # ورود کاربر با Django auth
            user = User.objects.filter(username=profile.user.username)
            if not user.exists():

                return JsonResponse({
                    'status': 'error',
                    'message': 'کاربر یافت نشد'
                }, status=404)

            user = user.first()
            login(request, user)
            
            # پاسخ موفق
            return JsonResponse({
                'status': 'success',
                'message': 'ورود با موفقیت انجام شد',
                'redirect_url': '/',

            }, status=200)
            
        except Profile.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'کاربر یافت نشد'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطای سیستمی: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'روش ارسال باید POST باشد'
    }, status=405)

    
def logout_user(request):
    """
    Logs out the user and redirects them to the home page or a specified page.
    """
    logout(request)  # Logs out the user
    return redirect('authentication:sign-in')


def register_page(request):
    logo ,description = get_info()

    return render(request,'sign-up.html',{'logo':logo,'app_description':description})



def register_api(request):

    if request.method == 'POST':
        try:
            phone = request.POST.get('phone')
            f_name = request.POST.get('f_name')
            l_name = request.POST.get('l_name')
            password = request.POST.get('new_password2')
            password_confirmation = request.POST.get('confirm-password')
            # اعتبارسنجی و ثبت‌نام
            if not password or not password_confirmation:
                return JsonResponse({
                    'status': 'error',
                    'message': 'خطا در ثبت‌نام : رمز عبور الزامی است.'
                }, status=400)
            
            if password!=password_confirmation:
                return JsonResponse({
                    'status': 'error',
                    'message': 'خطا در ثبت‌نام : رمز عبور باید یکسان باشد.'
                }, status=400)
            
            is_phone = bool(re.match(r'^09[0-9]{9}$', phone))
            if is_phone:
                phone_filter = Profile.objects.filter(phone=phone)
                if phone_filter.exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'خطا در ثبت‌نام : اکانتی با این شماره وجود دارد'
                    }, status=400)
            else:
                user_filter = User.objects.filter(username=phone)
                if user_filter.exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'خطا در ثبت‌نام : اکانتی با این نام وجود دارد'
                    }, status=400)

            user = User.objects.create(
                username=phone,
                password=password
            )
            password_hash = make_password(password=password)

            profile = Profile.objects.create(
                user=user,
                first_name=f_name,
                last_name=l_name,
                phone='09120000000',
                password_hash= password_hash
            )



            # login(request,profile.user)  # Logs out the user
                
            return JsonResponse({
                'status': 'success',
                'message': 'ثبت‌نام با موفقیت انجام شد!',
                'redirect_url': '/authentication/profile-page'
            },status = 200)
    
        except:
            return JsonResponse({
                'status': 'error',
                'message': 'خطا در ثبت‌نام'
            }, status=400)
    
    return JsonResponse({'message': 'Method not allowed'}, status=405)



@login_required(login_url='authentication:sign-in')
def show_profile_page(request):
    profile = request.user.profile
    context = {
        "profiles": Profile.objects.all() if profile.is_admin() else [],
    }
    return render(request,'profile.html',context)

def reset_password(request):
    logo ,description = get_info()
    
    return render(request,'reset_password.html',{'logo':logo,'app_description':description})



@login_required
def admin_change_password(request, pk):
    if not request.user.profile.is_admin():
        return redirect("profile")

    if request.method == "POST":
        profile = get_object_or_404(Profile, pk=pk)
        new_password = request.POST.get("password")

        profile.password_hash = make_password(new_password)
        profile.save()

    return redirect("profile")


@login_required
def delete_user(request, pk):
    if not request.user.profile.is_admin():
        return redirect("profile")

    profile = get_object_or_404(Profile, pk=pk)

    # delete Django user too
    if profile.user:
        profile.user.delete()

    profile.delete()

    return redirect("authentication:profile")