# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-19 18:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anno', '0004_auto_20171012_1209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='anno',
            name='schema_version',
            field=models.CharField(default='1.1.0', max_length=128),
        ),
    ]
