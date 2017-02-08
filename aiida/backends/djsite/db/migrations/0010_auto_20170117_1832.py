# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0009_dbnodefile_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dbnodefile',
            name='file',
            field=models.ForeignKey(related_name='dbnodefiles', on_delete=django.db.models.deletion.PROTECT, to='db.DbFile', null=True),
            preserve_default=True,
        ),
    ]
