# Generated manually for PlateScan integration

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0004_vehicle_is_active"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ai", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlateScan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(default="manual", max_length=20)),
                ("image", models.ImageField(blank=True, null=True, upload_to="plate_scans/%Y/%m/")),
                (
                    "annotated_image",
                    models.ImageField(blank=True, null=True, upload_to="plate_scans/annotated/%Y/%m/"),
                ),
                ("registered_plate", models.CharField(blank=True, default="", max_length=64)),
                ("detected_vehicle_type", models.CharField(blank=True, default="", max_length=64)),
                ("detected_plate_text", models.CharField(blank=True, default="", max_length=128)),
                ("plate_match", models.BooleanField(default=False)),
                ("models_ready", models.BooleanField(default=True)),
                ("error_message", models.TextField(blank=True, default="")),
                ("raw_result", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="plate_scans",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="plate_scans",
                        to="vehicles.vehicle",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
