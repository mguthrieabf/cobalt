# Generated by Django 2.1 on 2020-04-04 23:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_dob'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='bbo_name',
            field=models.TextField(blank='True', max_length=20, null=True, verbose_name='BBO Username'),
        ),
    ]