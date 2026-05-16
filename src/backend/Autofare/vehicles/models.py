from django.db import models
from django.conf import settings

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('car', 'Car'),
        ('truck', 'Truck'),
        ('motorcycle', 'Motorcycle'),
        ('bus', 'Bus'),
        ('minibus', 'Minibus'),
        ('van', 'Van'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    license_plate = models.CharField(max_length=20, unique=True)
    model_label = models.CharField(max_length=120, blank=True, default="")
    color = models.CharField(max_length=50, blank=True, default="")
    is_active = models.BooleanField(default=True)

    @classmethod
    def get_owner_by_plate(cls, plate):
        try:
            vehicle = cls.objects.get(license_plate=plate)
            return vehicle.user
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_vehicle_by_plate(cls, plate):
        try:
            return cls.objects.get(license_plate=plate)
        except cls.DoesNotExist:
            return None
