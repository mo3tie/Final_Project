from django.urls import path
from django.http import HttpResponse

def trip_list(request):
    return HttpResponse("Trips list")

urlpatterns = [
    path('', trip_list, name='trip_list'),
]