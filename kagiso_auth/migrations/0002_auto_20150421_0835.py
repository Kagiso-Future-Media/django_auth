# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kagiso_auth', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kagisouser',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
            preserve_default=True,
        ),
    ]
