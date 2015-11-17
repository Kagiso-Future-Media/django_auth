# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('kagiso_auth', '0002_auto_20150421_0835'),
    ]

    operations = [
        migrations.AddField(
            model_name='kagisouser',
            name='profile',
            field=jsonfield.fields.JSONField(null=True),
            preserve_default=True,
        ),
    ]
