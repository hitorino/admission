# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-22 11:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('msknet_censorship', '0002_auto_20161109_0116'),
    ]

    operations = [
        migrations.AddField(
            model_name='commit',
            name='is_under_review',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='question',
            name='answer_type',
            field=models.CharField(default='text', max_length=20),
        ),
    ]
