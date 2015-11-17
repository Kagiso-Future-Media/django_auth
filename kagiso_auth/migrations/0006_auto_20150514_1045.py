# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kagiso_auth', '0005_kagisouser_email_confirmed'),
    ]

    operations = [
        migrations.AddField(
            model_name='kagisouser',
            name='first_name',
            field=models.CharField(null=True, max_length=100, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='kagisouser',
            name='is_staff',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='kagisouser',
            name='last_name',
            field=models.CharField(null=True, max_length=100, blank=True),
            preserve_default=True,
        ),
    ]
