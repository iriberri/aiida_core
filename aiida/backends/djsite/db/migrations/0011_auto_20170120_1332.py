# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0010_auto_20170117_1832'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dbrepository',
            old_name='repo_name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='dbrepository',
            old_name='repo_uuid',
            new_name='uuid',
        ),
    ]
