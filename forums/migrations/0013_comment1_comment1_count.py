# Generated by Django 3.0.8 on 2020-07-13 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forums", "0012_auto_20200713_1049"),
    ]

    operations = [
        migrations.AddField(
            model_name="comment1",
            name="comment1_count",
            field=models.IntegerField(default=0),
        ),
    ]
