# Generated by Django 3.0.8 on 2020-07-26 13:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="CongressDownloads", new_name="CongressDownload",
        ),
    ]