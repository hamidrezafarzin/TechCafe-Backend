from django.contrib import admin
from gathering.models import Gathering, Photo, GatheringUser, Discount
import os

# Register your models here.


class GatheringAdmin(admin.ModelAdmin):
    search_fields = ["title", "presenter"]
    list_filter = ["title", "date", "is_held", "is_online", "is_occupied"]
    ordering = [
        "-date",
    ]
    list_display = (
        "title",
        "price",
        "date",
        "max_seats",
        "is_held",
        "is_online",
        "is_occupied",
    )


class GatheringUserAdmin(admin.ModelAdmin):
    search_fields = ["gathering__id", "gathering__title", "user__phone", "uuid"]
    list_filter = ["gathering", "check_in", "discount"]
    list_display = ("user", "user_full_name", "gathering", "uuid", "check_in")
    readonly_fields = ["uuid", "created_date", "updated_date"]

    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class PhotoAdmin(admin.ModelAdmin):
    search_fields = ["gathering__id", "image", "user"]
    list_display = [
        "image",
    ]


class DiscountAdmin(admin.ModelAdmin):
    search_fields = ["code", "gathering__title"]
    list_filter = ["status"]
    list_display = ("code", "gathering", "discount_percentage", "status")

    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


admin.site.register(Gathering, GatheringAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(GatheringUser, GatheringUserAdmin)
admin.site.register(Discount, DiscountAdmin)
