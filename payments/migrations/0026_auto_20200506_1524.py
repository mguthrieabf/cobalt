# Generated by Django 2.1 on 2020-05-06 05:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0025_auto_20200506_1448'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organisationtransaction',
            name='payment_date',
        ),
        migrations.RemoveField(
            model_name='organisationtransaction',
            name='payment_reference',
        ),
        migrations.RemoveField(
            model_name='organisationtransaction',
            name='payment_status',
        ),
    ]