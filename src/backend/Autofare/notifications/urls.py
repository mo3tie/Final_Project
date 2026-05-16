from django.urls import path
from django.http import HttpResponse

def notifications_home(request):
    return HttpResponse("Notifications Home")

urlpatterns = [
    path('', notifications_home, name='notifications-home'),
]
