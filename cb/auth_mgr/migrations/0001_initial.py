# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-08-26 09:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermissionRepository',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='status', to='auth.Permission')),
            ],
            options={
                'db_table': 'cb_permission_repository',
                'default_permissions': (),
            },
        ),
    ]
