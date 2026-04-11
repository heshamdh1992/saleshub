from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import StaffProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Extra Info", {"fields": ("full_name",)}),
    )
    list_display = ("username", "full_name", "email", "is_staff", "is_active")
    search_fields = ("username", "full_name", "email")


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "merchant", "role", "created_at")
    list_filter = ("role", "merchant")
    search_fields = ("user__username", "user__full_name", "merchant__name")