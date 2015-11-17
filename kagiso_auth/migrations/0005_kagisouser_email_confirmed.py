# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kagiso_auth', '0004_auto_20150422_0903'),
    ]

    operations = [
        migrations.AddField(
            model_name='kagisouser',
            name='email_confirmed',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
    ]
