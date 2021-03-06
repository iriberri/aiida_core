# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This allows to manage profiles from command line.
"""
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo
from aiida.cmdline.params import options
from aiida.control.postgres import Postgres


@verdi.group('profile')
def verdi_profile():
    """Inspect and manage the configured profiles."""
    pass


@verdi_profile.command("list")
def profile_list():
    """
    Displays list of all available profiles.
    """

    from aiida.common.setup import get_profiles_list, get_default_profile, AIIDA_CONFIG_FOLDER
    from aiida.common.exceptions import ConfigurationError

    echo.echo_info('Configuration folder: {}'.format(AIIDA_CONFIG_FOLDER))

    try:
        default_profile = get_default_profile()
    except ConfigurationError as err:
        err_msg = ("Stopping: {}\n"
                   "Note: if no configuration file was found, it means that you have not run\n"
                   "'verdi setup' yet to configure at least one AiiDA profile.".format(err.message))
        echo.echo_critical(err_msg)

    if default_profile is None:
        echo.echo_critical("### No default profile configured yet, run 'verdi install'! ###")
    else:
        echo.echo_info('The default profile is highlighted and marked by the * symbol')

    for profile in get_profiles_list():
        color_id = ''
        if profile == default_profile:
            symbol = '*'
            color_id = 'green'
        else:
            symbol = ' '

        click.secho('{} {}'.format(symbol, profile), fg=color_id)


@verdi_profile.command("setdefault")
@click.argument('profile_name', nargs=1, type=click.STRING)
def profile_setdefault(profile_name):
    """
    Set the passed profile as default profile in aiida config file.
    """
    from aiida.common.setup import set_default_profile
    set_default_profile(profile_name, force_rewrite=True)


@verdi_profile.command("delete")
@options.FORCE(help='to skip any questions/warnings about loss of data')
@click.argument('profiles', nargs=-1, type=click.STRING)
def profile_delete(force, profiles):
    """
    Delete PROFILES separated by space from aiida config file
    along with its associated database and repository.
    """
    from aiida.common.setup import get_or_create_config, update_config
    import os.path
    from urlparse import urlparse

    echo.echo('profiles: {}'.format(', '.join(profiles)))

    confs = get_or_create_config()
    available_profiles = confs.get('profiles', {})
    users = [available_profiles[name].get('AIIDADB_USER', '') for name in available_profiles.keys()]

    for profile_name in profiles:
        try:
            profile = available_profiles[profile_name]
        except KeyError:
            echo.echo_info("Profile '{}' does not exist".format(profile_name))
            continue

        postgres = Postgres(port=profile.get('AIIDADB_PORT'), interactive=True, quiet=False)
        postgres.dbinfo["user"] = profile.get('AIIDADB_USER')
        postgres.dbinfo["host"] = profile.get('AIIDADB_HOST')
        postgres.determine_setup()

        import json
        echo.echo(json.dumps(postgres.dbinfo, indent=4))

        db_name = profile.get('AIIDADB_NAME', '')
        if not postgres.db_exists(db_name):
            echo.echo_info("Associated database '{}' does not exist.".format(db_name))
        elif force or click.confirm("Delete associated database '{}'?\n" \
                                    "WARNING: All data will be lost.".format(db_name)):
            echo.echo_info("Deleting database '{}'.".format(db_name))
            postgres.drop_db(db_name)

        user = profile.get('AIIDADB_USER', '')
        if not postgres.dbuser_exists(user):
            echo.echo_info("Associated database user '{}' does not exist.".format(user))
        elif users.count(user) > 1:
            echo.echo_info("Associated database user '{}' is used by other profiles " \
                  "and will not be deleted.".format(user))
        elif force or click.confirm("Delete database user '{}'?".format(user)):
            echo.echo_info("Deleting user '{}'.".format(user))
            postgres.drop_dbuser(user)

        repo_uri = profile.get('AIIDADB_REPOSITORY_URI', '')
        repo_path = urlparse(repo_uri).path
        repo_path = os.path.expanduser(repo_path)
        if not os.path.isabs(repo_path):
            echo.echo_info("Associated file repository '{}' does not exist." \
                  .format(repo_path))
        elif not os.path.isdir(repo_path):
            echo.echo_info("Associated file repository '{}' is not a directory." \
                  .format(repo_path))
        elif force or click.confirm("Delete associated file repository '{}'?\n" \
                                    "WARNING: All data will be lost.".format(repo_path)):
            echo.echo_info("Deleting directory '{}'.".format(repo_path))
            import shutil
            shutil.rmtree(repo_path)

        if force or click.confirm("Delete configuration for profile '{}'?\n" \
                                  "WARNING: Permanently removes profile from the list of AiiDA profiles." \
                                          .format(profile_name)):
            echo.echo_info("Deleting configuration for profile '{}'.".format(profile_name))
            del available_profiles[profile_name]
            update_config(confs)
