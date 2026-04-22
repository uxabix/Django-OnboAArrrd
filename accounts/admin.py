from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Roles

# ------------------------
# CustomUserAdmin
# ------------------------
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'get_mentor', 'role', 'is_staff', 'is_active', 'status')
    list_filter = ('is_staff', 'is_active', 'status', 'role')
    
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role', 'mentor', 'stars')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
'fields': ('email', 'first_name', 'last_name', 'role', 'mentor', 'stars', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    # Funkcja wyświetlająca mentora w list_display
    def get_mentor(self, obj):
        return obj.mentor  # Wyświetla powiązanego użytkownika
    get_mentor.short_description = 'Mentor'

# ------------------------
# RolesAdmin
# ------------------------
class RolesAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'name', 'description')
    search_fields = ('name',)
    ordering = ('role_id', 'name')

# ------------------------
# Rejestracja modeli
# ------------------------
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Roles, RolesAdmin)
