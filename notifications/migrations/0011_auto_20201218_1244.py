# Generated by Django 3.0.9 on 2020-12-18 01:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0010_remove_abstractemail_actor"),
    ]

    operations = [
        migrations.AddField(
            model_name="abstractemail",
            name="reply_to",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                null=True,
                verbose_name="Reply To",
            ),
        ),
        migrations.AlterField(
            model_name="abstractemail",
            name="recipient",
            field=models.CharField(max_length=100, verbose_name="Recipients"),
        ),
    ]