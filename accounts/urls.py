from django.urls import path

from . import hr_views, views

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/logged/", views.logged, name="logged"),
    path(
        "accounts/password-first-change/",
        views.force_first_password_change,
        name="force_first_password_change",
    ),
    path("hr/", hr_views.hr_dashboard, name="hr_dashboard"),
    path("hr/dodaj/", hr_views.hr_add_employee, name="hr_add_employee"),
    path("hr/zwolnij/<int:user_id>/", hr_views.hr_terminate_employee, name="hr_terminate_employee"),
    path("hr/aktywuj/<int:user_id>/", hr_views.hr_reactivate_employee, name="hr_reactivate_employee"),
    path("hr/rola/<int:user_id>/", hr_views.hr_change_role, name="hr_change_role"),
    path("hr/change-own-password/", hr_views.hr_change_own_password, name="hr_change_own_password"),
    path("hr/reset-password/<int:user_id>/", hr_views.hr_reset_user_password, name="hr_reset_user_password"),
]