# Generated by Django 3.0.9 on 2020-12-12 22:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("payments", "0041_auto_20201212_1551"),
    ]

    operations = [
        migrations.AlterField(
            model_name="membertransaction",
            name="member",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="primary_member",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
    ]
