from django.conf import settings
from django.db import models


class PlateScan(models.Model):
    SOURCE_SIGNUP = "signup"
    SOURCE_MANUAL = "manual"
    SOURCE_ADMIN = "admin_gate"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="plate_scans",
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plate_scans",
    )
    source = models.CharField(max_length=20, default=SOURCE_MANUAL)
    image = models.ImageField(upload_to="plate_scans/%Y/%m/", blank=True, null=True)
    annotated_image = models.ImageField(
        upload_to="plate_scans/annotated/%Y/%m/", blank=True, null=True
    )
    registered_plate = models.CharField(max_length=64, blank=True, default="")
    detected_vehicle_type = models.CharField(max_length=64, blank=True, default="")
    detected_plate_text = models.CharField(max_length=128, blank=True, default="")
    plate_match = models.BooleanField(default=False)
    models_ready = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, default="")
    raw_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Scan #{self.pk} user={self.user_id} plate={self.detected_plate_text!r}"
