from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password


# Create your models here.
# Extending User Model Using a One-To-One Link
class RoleEnum(models.TextChoices):
    ADMIN = "admin", "Admin"
    USER = "کاربر", "User"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    first_name = models.CharField(max_length=120, null=True, blank=True, verbose_name="نام")
    last_name = models.CharField(max_length=120, null=True, blank=True, verbose_name="نام خانوادگی")
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True, verbose_name="ایمیل")
    phone = models.CharField(max_length=50, unique=False, null=False, blank=False, verbose_name="شماره همراه")
    password_hash = models.CharField(max_length=255, null=True, blank=True, verbose_name="رمز عبور")
    is_active = models.BooleanField(default=True, verbose_name="آیا اکانت فعال است")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ثبت نام")
    avatar = models.ImageField(default='assets/profile_images/vipa_default.jpg', upload_to='assets/profile_images/')

    role = models.CharField(max_length=10, choices=RoleEnum.choices, default=RoleEnum.USER, verbose_name="نقش کاربر")


    class Meta:
        verbose_name = "پروفایل کاربر"
        verbose_name_plural = "پروفایل کاربران"

    def set_password(self, password: str):
        """Set hashed password."""
        self.password_hash = make_password(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password is correct."""
        return check_password(password, self.password_hash)

    def is_admin(self) -> bool:
        """Check if the user is admin."""
        return self.role == RoleEnum.ADMIN 
    

    # Override save() method to automatically create User if user_id is None
    def save(self, *args, **kwargs):
        # If user_id is null, create a new User
        if not self.user:
            user = User.objects.create(
                username=self.phone,  # Using phone as the username
                is_active=self.is_active,
                password=make_password(self.password_hash)  # Set password hash
            )
            self.user = user  # Assign the newly created user to the profile
            self.password_hash = make_password(self.password_hash)
        super(Profile, self).save(*args, **kwargs)



    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    