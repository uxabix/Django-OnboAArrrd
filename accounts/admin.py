from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Roles

# ------------------------
# CustomUserAdmin
# ------------------------
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'get_mentor', 'role_id', 'is_staff', 'is_active', 'status_id')
    list_filter = ('is_staff', 'is_active', 'status_id', 'role_id')
    
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role_id', 'mentor_id')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role_id', 'mentor_id', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    # Funkcja wyświetlająca mentora w list_display
    def get_mentor(self, obj):
        return obj.mentor_id  # Wyświetla powiązanego użytkownika
    get_mentor.short_description = 'Mentor'

# ------------------------
# RolesAdmin
# ------------------------
class RolesAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'name', 'description')
    search_fields = ('name',)
    ordering = ('role_id',)

# ------------------------
# Rejestracja modeli
# ------------------------
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Roles, RolesAdmin)
