import django.core.validators
from django.db import migrations, models

import users.models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="photo",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=users.models.profile_photo_upload,
                validators=[
                    django.core.validators.FileExtensionValidator(
                        ["jpg", "jpeg", "png", "webp"]
                    )
                ],
            ),
        ),
    ]
