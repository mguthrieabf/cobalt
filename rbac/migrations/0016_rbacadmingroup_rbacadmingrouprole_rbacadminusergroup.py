# Generated by Django 2.2.13 on 2020-06-09 01:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("rbac", "0015_rbacappmodelaction"),
    ]

    operations = [
        migrations.CreateModel(
            name="RBACAdminGroup",
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
                ("group_name", models.CharField(max_length=50)),
                ("description", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="RBACAdminUserGroup",
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
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="rbac.RBACGroup"
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RBACAdminGroupRole",
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
                ("app", models.CharField(max_length=15)),
                ("model", models.CharField(max_length=15)),
                ("model_id", models.IntegerField(blank=True, null=True)),
                ("action", models.CharField(max_length=15)),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="rbac.RBACGroup"
                    ),
                ),
            ],
        ),
    ]
