# Generated by Django 3.0.8 on 2020-08-01 03:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("forums", "0017_auto_20200714_1721"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="comment1", options={"ordering": ["-created_date"]},
        ),
        migrations.AlterModelOptions(
            name="comment2", options={"ordering": ["-created_date"]},
        ),
        migrations.AlterModelOptions(
            name="post", options={"ordering": ["-created_date"]},
        ),
    ]
