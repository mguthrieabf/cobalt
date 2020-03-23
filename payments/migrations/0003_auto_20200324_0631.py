# Generated by Django 2.1 on 2020-03-23 19:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_auto_20200323_1606'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='comment',
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_brand',
            field=models.CharField(max_length=10, null=True, verbose_name='Card brand'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_country',
            field=models.CharField(max_length=5, null=True, verbose_name='Card Country'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_currency',
            field=models.CharField(max_length=3, null=True, verbose_name='Card Native Currency'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_exp_month',
            field=models.IntegerField(null=True, verbose_name='Card Expiry Month'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_exp_year',
            field=models.IntegerField(null=True, verbose_name='Card Expiry Year'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_last4',
            field=models.CharField(max_length=4, null=True, verbose_name='Card Last 4 Digits'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_method',
            field=models.CharField(max_length=40, null=True, verbose_name='Stripe Payment Method'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_receipt_url',
            field=models.CharField(max_length=200, null=True, verbose_name='Receipt URL'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_reference',
            field=models.CharField(max_length=40, null=True, verbose_name='Stripe Payment Intent'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='member',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.CharField(choices=[('Initiated', 'Started - payment needs made'), ('Intent', 'Intent - received customer intent to pay from Stripe'), ('Complete', 'Success - payment completed successfully'), ('Failed', 'Failed - payment failed')], default='Initiated', max_length=9),
        ),
    ]