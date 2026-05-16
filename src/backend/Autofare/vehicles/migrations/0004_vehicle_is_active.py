from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0003_vehicle_model_label_color"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
