# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0007_remove_dbrepository_uuid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dbnodefile',
            name='metadata',
        ),
    ]
