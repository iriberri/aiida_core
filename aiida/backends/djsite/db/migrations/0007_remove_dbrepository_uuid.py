# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0006_dbnodefile_metadata'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dbrepository',
            name='uuid',
        ),
    ]
