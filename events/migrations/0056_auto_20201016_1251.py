# Generated by Django 3.0.9 on 2020-10-16 01:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0055_auto_20201015_1255'),
    ]

    operations = [
        migrations.AlterField(
            model_name='congress',
            name='early_payment_discount_date',
            field=models.DateField(blank=True, null=True, verbose_name='Last day for early discount'),
        ),
        migrations.AlterField(
            model_name='congress',
            name='entry_close_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='congress',
            name='entry_open_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='congress',
            name='senior_date',
            field=models.DateField(blank=True, null=True, verbose_name='Date for age check'),
        ),
        migrations.AlterField(
            model_name='congress',
            name='youth_payment_discount_date',
            field=models.DateField(blank=True, null=True, verbose_name='Date for age check'),
        ),
    ]
