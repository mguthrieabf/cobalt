# Generated by Django 3.0.9 on 2020-12-21 04:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0081_auto_20201221_1456"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evententry",
            name="notes",
            field=models.TextField(blank=True, null=True, verbose_name="Notes"),
        ),
    ]