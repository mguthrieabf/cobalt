# Generated by Django 2.2.13 on 2020-06-23 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forums", "0010_forumfollow"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment1",
            name="last_change_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="comment2",
            name="last_change_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="post",
            name="last_change_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
