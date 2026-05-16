from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def home(request):
    return HttpResponse("Welcome to AutoFare")


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/payment/", include("payment.urls")),
    path("api/vehicles/", include("vehicles.urls")),
    path("api/ai/", include("ai.urls")),
    path('trips/', include('trips.urls')),
    path('payment/', include('payment.urls')),
    path('ai/', include('ai.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('violations/', include('violations.urls')),
    path('notifications/', include('notifications.urls')),
    path('adminelweb/', include('Adminelweb.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
