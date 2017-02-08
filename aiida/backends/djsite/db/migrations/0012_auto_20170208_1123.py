# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0011_auto_20170120_1332'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dbfile',
            name='nodes',
        ),
        migrations.RemoveField(
            model_name='dbfile',
            name='repository',
        ),
        migrations.AlterUniqueTogether(
            name='dbnodefile',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='dbnodefile',
            name='file',
        ),
        migrations.DeleteModel(
            name='DbFile',
        ),
        migrations.RemoveField(
            model_name='dbnodefile',
            name='node',
        ),
        migrations.DeleteModel(
            name='DbNodeFile',
        ),
        migrations.DeleteModel(
            name='DbRepository',
        ),
    ]
