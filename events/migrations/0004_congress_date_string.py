# Generated by Django 3.0.8 on 2020-07-26 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_auto_20200727_0920"),
    ]

    operations = [
        migrations.AddField(
            model_name="congress",
            name="date_string",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Dates"
            ),
        ),
    ]
