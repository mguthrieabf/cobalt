# Generated by Django 2.1 on 2020-03-22 04:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('masterpoints', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MasterpointDetails',
        ),
        migrations.DeleteModel(
            name='MasterpointsClubs',
        ),
        migrations.DeleteModel(
            name='MasterpointsCopy',
        ),
    ]
