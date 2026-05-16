from django.urls import path
from django.http import HttpResponse

def violations_home(request):
    return HttpResponse("Violations Home")

urlpatterns = [
    path('', violations_home, name='violations-home'),
]
