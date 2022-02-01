from django.contrib import admin

from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email')
    search_fields = ('email', 'username')
    list_filter = ('email', 'username')
    empty_value_display = '-empty-'


admin.site.register(User, UserAdmin)
