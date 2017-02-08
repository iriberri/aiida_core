# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0004_auto_20170117_1415'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dbnodefile',
            name='metadata',
        ),
    ]
