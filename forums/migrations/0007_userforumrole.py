# Generated by Django 2.1 on 2020-05-06 05:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("forums", "0006_auto_20200502_1048"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserForumRole",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("Poster", "Poster - can create a new post"),
                            ("Responder", "Responder - can reply to a post"),
                            ("Moderator", "Moderator - can manage the forum"),
                        ],
                        max_length=20,
                        verbose_name="User role in forum",
                    ),
                ),
                (
                    "rule",
                    models.CharField(
                        choices=[
                            ("Allow", "Allows a user to perform a role"),
                            ("Block", "Blocks a user from performing a role"),
                        ],
                        max_length=5,
                        verbose_name="Type of Rule",
                    ),
                ),
                (
                    "forum",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="forums.Forum"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
