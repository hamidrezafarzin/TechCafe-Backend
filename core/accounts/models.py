from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from accounts.tasks import send_welcome
from validators.fieldvalidators import FieldValidators
from validators.volumevalidator import VolumeValidator

# Define a custom user manager for the User model.
class UserManager(BaseUserManager):
    """
    Custom user model manager where phone is the unique identifier
    for authentication instead of usernames.
    """

    def create_user(self, phone, password, **extra_fields):
        """
        Create and save a User with the given phone and password.
        """
        if not phone:
            raise ValueError(_("The phone must be set"))
        extra_fields.setdefault("is_active", True)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone, password, **extra_fields):
        """
        Create and save a SuperUser with the given phone and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_ban", False)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(phone, password, **extra_fields)

# Define the custom User model.
class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(
        _("Phone"),
        max_length=11,
        unique=True,
        validators=[
            FieldValidators.iranian_phone_validator,
            FieldValidators.xss_validator,
        ],
        blank=False,
        null=False,
    )
    email = models.EmailField(
        validators=[FieldValidators.xss_validator], unique=True, blank=True, null=True
    )
    first_name = models.CharField(
        max_length=255,
        validators=[FieldValidators.xss_validator],
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        max_length=255,
        validators=[FieldValidators.xss_validator],
        blank=False,
        null=False,
    )
    job_field = models.CharField(
        max_length=100,
        validators=[FieldValidators.xss_validator],
        blank=True,
        null=True,
    )
    avatar = models.ImageField(
        upload_to="avatars",
        validators=[VolumeValidator.validate_avatar_size],
        blank=True,
        null=True,
    )
    languages = models.ManyToManyField("languages", blank=True)
    frameworks = models.ManyToManyField("frameworks", blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_ban = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone

    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"

# Define models for Languages and Frameworks.
class Languages(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name

class Frameworks(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name

# Signal handler to create a user profile and send a welcome message on user creation.
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        send_welcome.delay(instance.phone, instance.first_name)
