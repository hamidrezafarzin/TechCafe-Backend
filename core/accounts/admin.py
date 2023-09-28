from django.contrib import admin
from .models import User, Languages, Frameworks
from django.contrib.auth.admin import UserAdmin


class UserAdminConfig(UserAdmin):
    model = User
    search_fields = ("phone", "first_name", "last_name")
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "created_date",
        "is_ban",
    )
    ordering = ("-created_date",)
    list_display = (
        "phone",
        "first_name",
        "last_name",
        "job_field",
        "is_superuser",
        "is_staff",
        "is_ban",
        "is_active",
        "created_date",
    )

    fieldsets = (
        (
            "Account Data",
            {
                "fields": (
                    "phone",
                    "email",
                    "first_name",
                    "last_name",
                    "job_field",
                    "avatar",
                ),
            },
        ),
        ("languages &frameworks ", {"fields": ("languages", "frameworks")}),
        ("Event Cancellation Count", {"fields": ("is_ban",)}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser")}),
        (
            "Group Permissions",
            {
                "fields": (
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone",
                    "first_name",
                    "last_name",
                    "job_field",
                    "frameworks",
                    "languages",
                    "avatar",
                    "is_ban",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


admin.site.site_header = "Tech Cafe Admin Panel"
admin.site.register(User, UserAdminConfig)
admin.site.register(Languages)
admin.site.register(Frameworks)
