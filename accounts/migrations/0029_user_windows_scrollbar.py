# Generated by Django 3.0.9 on 2020-12-25 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0028_user_system_number_search"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="windows_scrollbar",
            field=models.BooleanField(
                default=False, verbose_name="Show old scrollbar on Windows"
            ),
        ),
    ]
