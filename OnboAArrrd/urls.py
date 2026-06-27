"""Root URLConf wiring admin, authentication, accounts, chat, and onboarding."""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('accounts.urls')),
    path('chat/', include('chat.urls')),  # <--- DOŁĄCZENIE APP CHAT
    path('', include('onboarding.urls')),  # <--- DOŁĄCZENIE APP ONBOARDING
]

# Add static files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
