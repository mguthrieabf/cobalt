# Generated by Django 2.1 on 2020-05-02 00:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0021_auto_20200429_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autotopupconfig',
            name='auto_amount',
            field=models.IntegerField(blank=True, null=True, verbose_name='Auto Top Up Amount'),
        ),
        migrations.AlterField(
            model_name='autotopupconfig',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=25, null=True, verbose_name='Stripe Customer Id'),
        ),
        migrations.AlterField(
            model_name='membertransaction',
            name='description',
            field=models.CharField(blank=True, max_length=80, null=True, verbose_name='Transaction Description'),
        ),
        migrations.AlterField(
            model_name='membertransaction',
            name='organisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organisations.Organisation'),
        ),
        migrations.AlterField(
            model_name='membertransaction',
            name='other_member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='other_member', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='membertransaction',
            name='stripe_transaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='payments.StripeTransaction'),
        ),
        migrations.AlterField(
            model_name='organisationtransaction',
            name='description',
            field=models.CharField(blank=True, max_length=80, null=True, verbose_name='Transaction Description'),
        ),
        migrations.AlterField(
            model_name='organisationtransaction',
            name='member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='organisationtransaction',
            name='organisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='primary_org', to='organisations.Organisation'),
        ),
        migrations.AlterField(
            model_name='organisationtransaction',
            name='other_organisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='secondary_org', to='organisations.Organisation'),
        ),
        migrations.AlterField(
            model_name='organisationtransaction',
            name='payment_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Payment Date'),
        ),
        migrations.AlterField(
            model_name='organisationtransaction',
            name='payment_reference',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Payment Reference'),
        ),
        migrations.AlterField(
            model_name='organisationtransaction',
            name='stripe_transaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='payments.StripeTransaction'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='route_code',
            field=models.CharField(blank=True, max_length=4, null=True, verbose_name='Internal routing code for callback'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='route_payload',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='Payload to return to callback'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='stripe_brand',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Card brand'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='stripe_country',
            field=models.CharField(blank=True, max_length=5, null=True, verbose_name='Card Country'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='stripe_currency',
            field=models.CharField(blank=True, max_length=3, null=True, verbose_name='Card Native Currency'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='stripe_exp_month',
            field=models.IntegerField(blank=True, null=True, verbose_name='Card Expiry Month'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='stripe_exp_year',
            field=models.IntegerField(blank=True, null=True, verbose_name='Card Expiry Year'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='stripe_last4',
            field=models.CharField(blank=True, max_length=4, null=True, verbose_name='Card Last 4 Digits'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='stripe_method',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='Stripe Payment Method'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='stripe_receipt_url',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Receipt URL'),
        ),
        migrations.AlterField(
            model_name='stripetransaction',
            name='stripe_reference',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='Stripe Payment Intent'),
        ),
    ]