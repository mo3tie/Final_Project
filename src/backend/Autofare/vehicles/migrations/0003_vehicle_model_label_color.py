from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0002_alter_vehicle_vehicle_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="model_label",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="color",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
    ]
