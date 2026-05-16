from django.urls import path
from django.http import HttpResponse

def adminelweb_home(request):
    return HttpResponse("Admin Web Home")

urlpatterns = [
    path('', adminelweb_home, name='adminelweb-home'),
]
