# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('kagiso_auth', '0003_kagisouser_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='kagisouser',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 22, 9, 3, 27, 81025, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='kagisouser',
            name='date_joined',
            field=models.DateTimeField(),
            preserve_default=True,
        ),
    ]
