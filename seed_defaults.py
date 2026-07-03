import os
import django
from django.core.files import File




os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SekeSepidar.settings")  # VERY IMPORTANT
django.setup()
from django.contrib.auth.models import User
from dashboard.models import BaseSettings, Page, SubPage
from authentication.models import Profile, RoleEnum
from django.contrib.auth.hashers import make_password


# بررسی و ایجاد Superuser
def get_or_create_superuser():
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin'

    user_obj = User.objects.filter(
        username=username,
        email=email,

    )


    if not User.objects.exists() or not user_obj.exists():

        
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        password_hash = make_password(password=password)
        profile = Profile.objects.create(
            user=user,
            first_name='مدیر',
            last_name='سیستم',
            phone='09120000000',
            password_hash= password_hash,
            role = RoleEnum.ADMIN
        )
        print(f"✅ Superuser ایجاد شد:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        return user , profile
    else:
        profile = user_obj.first().profile
        print("ℹ️ کاربری از قبل وجود دارد")
        return User.objects.first(),profile


# اجرا
current_user, current_profile = get_or_create_superuser()
print(f"Selected User: {current_user.username}")

# ✅ تنظیمات پیش‌فرض سایت
print("Inserting App Settings defaults...")
settings, created = BaseSettings.objects.get_or_create(
    pk=1,
    defaults={
        'name': 'سیستم اتصال سپیدار',
        'name_en': 'Sepidar System',
        'description': 'سیستم مدیریتی جهت اتصال و فاکتور های فروش',
        
        # محدودیت‌ها
        'max_datasets': 10,
        'max_users': 100,
        'max_classes_per_dataset': 50,
        'max_images_per_dataset': 10000,
        'max_image_size': 10, #MB
        
        # ظاهر
        'primary_color': '#3498db',
        'secondary_color': '#2ecc71',
        'theme_mode': 'light',
        
        # امنیت
        'session_timeout': 30, #min
        'max_login_attempts': 5,
        'password_min_length': 8,
        'require_email_verification': False,
        
        # سیستم
        'is_maintenance_mode': False,
        'allow_registration': True,

        'logo': 'assets\logo\logo20fullcolor.png'




    }
)
# اگه تنظیمات جدید ساخته شد، لوگو رو ست کن
if created:
    default_logo_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),  # مسیر فایل models.py
        'assets', 'logo', 'logo20fullcolor.png'
    )
    
    if os.path.exists(default_logo_path):
        with open(default_logo_path, 'rb') as f:
            settings.logo.save(
                'logo20fullcolor',
                File(f),
                save=True
            )
    print("Default logo set successfully!")


print("✅ Site Settings defaults Done.")




print("Inserting Menu defaults...")


pages_data = [

    {
        "name": "home_page",
        "label": "صفحه اصلی",
        "icon": """<i class="ki-duotone ki-ranking fs-2">
                        <span class="path1"></span>
                        <span class="path2"></span>
                        <span class="path3"></span>
                        <span class="path4"></span>
                        <span class="path5"></span>
                        <span class="path6"></span>
                        <span class="path7"></span>
                        <span class="path8"></span>
                    </i>""",
        "type": "item",
        "link": "/",
        "order" : 1,
    },

    {
        "name": "about",
        "label": "درباره نرم افزار",
        "icon": """<i class="ki-duotone ki-ranking fs-2">
                        <span class="path1"></span>
                        <span class="path2"></span>
                        <span class="path3"></span>
                        <span class="path4"></span>
                        <span class="path5"></span>
                        <span class="path6"></span>
                        <span class="path7"></span>
                        <span class="path8"></span>
                    </i>""",
        "type": "item",
        "link": "/about/about",
        "order" : 2,
    },
    
]

for page_data in pages_data:
    page, created = Page.objects.get_or_create(
        name=page_data['name'],
        created_by=current_user,
        defaults={
            'label': page_data['label'],
            'icon': page_data['icon'],
            'type': page_data['type'],
            'link': page_data.get('link', ''),
            'order': page_data['order'],
        }
    )

    if page_data['type'] == 'tree':
        for sub_data in page_data['subs']:
            SubPage.objects.get_or_create(
                parent_page=page,
                name=sub_data['name'],
                defaults={
                    'label': sub_data['label'],
                    'icon': sub_data['icon'],
                    'type': sub_data['type'],
                    'link': sub_data.get('link', ''),
                    'order': sub_data['order'],
                }
            )


print("✅ Default pages and subpages created.")

