# Generated by Django 2.1 on 2020-05-02 00:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0003_log_ip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='ip',
            field=models.CharField(blank='True', max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='message',
            field=models.CharField(blank='True', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='source',
            field=models.CharField(blank='True', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='sub_source',
            field=models.CharField(blank='True', max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='user',
            field=models.CharField(blank='True', max_length=30, null=True),
        ),
    ]
