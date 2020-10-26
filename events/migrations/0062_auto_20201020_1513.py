# Generated by Django 3.0.9 on 2020-10-20 04:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0061_auto_20201020_1127"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evententry",
            name="entry_status",
            field=models.CharField(
                choices=[("Pending", "Pending"), ("Complete", "Complete")],
                default="Pending",
                max_length=20,
                verbose_name="Entry Status",
            ),
        ),
    ]