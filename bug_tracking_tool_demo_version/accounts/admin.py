from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Bug, Notification, BugComment

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_developer', 'is_tester', 'experience', 'workload', 'project')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Bug)
admin.site.register(Notification)
admin.site.register(BugComment)
