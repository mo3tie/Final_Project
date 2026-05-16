from django.contrib import admin

from .models import PlateScan


@admin.register(PlateScan)
class PlateScanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "source",
        "registered_plate",
        "detected_plate_text",
        "plate_match",
        "models_ready",
        "created_at",
    )
    list_filter = ("source", "plate_match", "models_ready")
    search_fields = ("registered_plate", "detected_plate_text", "user__email")
    readonly_fields = ("created_at", "raw_result")
