# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-28 01:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('amazon_web', '0003_auto_20170428_0046'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='review',
            new_name='usr_review',
        ),
        migrations.RenameField(
            model_name='usr_review',
            old_name='review',
            new_name='review_content',
        ),
    ]