# Generated by Django 2.2.13 on 2020-06-10 04:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("rbac", "0019_auto_20200610_1346"),
    ]

    operations = [
        migrations.RenameField(
            model_name="rbacadmingroup", old_name="group_name", new_name="name_item",
        ),
        migrations.AddField(
            model_name="rbacadmingroup",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="rbacadmingroup",
            name="created_date",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="Create Date"
            ),
        ),
        migrations.AddField(
            model_name="rbacadmingroup",
            name="group_type",
            field=models.CharField(
                choices=[("Forum", "Forums"), ("Organisation", "Organisations")],
                default="x",
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="rbacadmingroup",
            name="name_qualifier",
            field=models.CharField(default="x", max_length=50),
            preserve_default=False,
        ),
    ]
