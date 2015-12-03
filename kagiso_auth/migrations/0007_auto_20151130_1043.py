# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kagiso_auth', '0006_auto_20150514_1045'),
    ]

    operations = [
        migrations.RenameField(
            model_name='kagisouser',
            old_name='date_joined',
            new_name='created',
        ),
        migrations.AddField(
            model_name='kagisouser',
            name='created_via',
            field=models.CharField(null=True, max_length=100, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='kagisouser',
            name='last_sign_in_via',
            field=models.CharField(null=True, max_length=100, blank=True),
            preserve_default=True,
        ),
    ]
