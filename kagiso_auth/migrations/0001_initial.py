# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='KagisoUser',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(verbose_name='last login', default=django.utils.timezone.now)),
                ('is_superuser', models.BooleanField(help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status', default=False)),
                ('email', models.EmailField(max_length=250, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', related_query_name='user', related_name='user_set', blank=True, verbose_name='groups', to='auth.Group')),
                ('user_permissions', models.ManyToManyField(help_text='Specific permissions for this user.', related_query_name='user', related_name='user_set', blank=True, verbose_name='user permissions', to='auth.Permission')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
