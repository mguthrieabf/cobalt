# Generated by Django 3.0.8 on 2020-08-07 04:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0029_rbacappmodelaction_description"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rbacappmodelaction",
            name="description",
            field=models.CharField(max_length=100),
        ),
    ]
