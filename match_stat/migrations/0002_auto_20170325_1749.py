# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-25 17:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('match_stat', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchinfo',
            name='matchid',
            field=models.BigIntegerField(primary_key=True, serialize=False, unique=True),
        ),
    ]
