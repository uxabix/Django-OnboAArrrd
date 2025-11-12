from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Roles

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'role_id', 'is_staff', 'is_active', 'status')
    list_filter = ('is_staff', 'is_active', 'status', 'role_id')
    
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role_id')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role_id', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

class RolesAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'name', 'description')
    search_fields = ('name',)
    ordering = ('role_id',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Roles, RolesAdmin)
