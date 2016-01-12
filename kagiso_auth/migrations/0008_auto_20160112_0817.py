# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kagiso_auth', '0007_auto_20151130_1043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kagisouser',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups', related_name='user_set', blank=True, to='auth.Group'),
        ),
        migrations.AlterField(
            model_name='kagisouser',
            name='last_login',
            field=models.DateTimeField(null=True, blank=True, verbose_name='last login'),
        ),
    ]
