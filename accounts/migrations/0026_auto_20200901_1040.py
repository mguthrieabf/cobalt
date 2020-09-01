# Generated by Django 3.0.9 on 2020-09-01 00:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0025_teammate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="teammate",
            name="team_mate",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="team_mate_team_mate",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="teammate",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="team_mate_user",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
