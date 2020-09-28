# Generated by Django 3.0.9 on 2020-09-28 00:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0044_auto_20200928_0947"),
    ]

    operations = [
        migrations.AddField(
            model_name="evententry",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="events.Category",
            ),
        ),
    ]
