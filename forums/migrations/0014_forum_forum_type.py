# Generated by Django 3.0.8 on 2020-07-13 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forums", "0013_comment1_comment1_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="forum",
            name="forum_type",
            field=models.CharField(
                choices=[
                    ("Discussion", "Discussion Forum"),
                    ("Announcement", "Announcement Forum"),
                    ("Club", "Club Forum"),
                ],
                default="Discussion",
                max_length=20,
                verbose_name="Forum Type",
            ),
        ),
    ]
