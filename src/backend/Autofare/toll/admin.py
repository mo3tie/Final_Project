from django.contrib import admin
from .models import Trip, Gate, Toll

# Register your models here.
admin.site.register(Trip)
admin.site.register(Gate)
admin.site.register(Toll)
