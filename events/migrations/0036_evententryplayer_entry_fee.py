# Generated by Django 3.0.9 on 2020-08-31 01:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0035_auto_20200831_1114"),
    ]

    operations = [
        migrations.AddField(
            model_name="evententryplayer",
            name="entry_fee",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name="Entry Fee",
            ),
        ),
    ]