# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0005_remove_dbnodefile_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='dbnodefile',
            name='metadata',
            field=models.TextField(default=b'{}'),
            preserve_default=True,
        ),
    ]
