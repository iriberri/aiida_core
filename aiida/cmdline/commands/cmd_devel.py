# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi devel` commands."""
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.params.types import TestModuleParamType
from aiida.cmdline.utils import decorators, echo
from aiida.common.exceptions import TestsNotAllowedError


@verdi.group('devel')
def verdi_devel():
    """Commands for developers."""
    pass


@decorators.with_dbenv()
def get_valid_test_paths():
    """
    Return a dictionary with the available test folders

    The content of the dict is:
        None for a simple folder test
        A list of strings for db tests, one for each test to run
    """
    from aiida.backends.tests import get_db_test_names

    db_prefix_raw = 'db'
    db_prefix = db_prefix_raw + '.'
    base_test_modules = [
        'aiida.scheduler',
        'aiida.transport',
        'aiida.common',
        'aiida.utils',
        'aiida.control',
        'aiida.cmdline.utils',
        'aiida.cmdline.params.types',
        'aiida.cmdline.params.options',
    ]

    valid_test_paths = {}

    db_test_list = get_db_test_names()

    for module in base_test_modules:
        valid_test_paths[module] = None

    for db_test in db_test_list:
        valid_test_paths['{}{}'.format(db_prefix, db_test)] = [db_test]

    valid_test_paths[db_prefix_raw] = db_test_list

    return valid_test_paths


@verdi_devel.command('describeproperties')
def devel_describeproperties():
    """
    List all valid properties that can be stored in the AiiDA config file.

    Only properties listed in the ``_property_table`` of ``aida.common.setup`` can be used.
    """
    from aiida.common.setup import _property_table, _NoDefaultValue

    for prop in sorted(_property_table.keys()):

        prop_name = _property_table[prop][1]
        prop_type = _property_table[prop][2]
        prop_default = _property_table[prop][3]
        prop_values = _property_table[prop][4]

        if prop_values is None:
            prop_values_str = ''
        else:
            prop_values_str = ' Valid values: {}.'.format(', '.join(str(_) for _ in prop_values))

        if isinstance(prop_default, _NoDefaultValue):
            prop_default_str = ''
        else:
            prop_default_str = ' (default: {})'.format(prop_default)

        echo.echo('* {} ({}): {}{}{}'.format(prop, prop_name, prop_type, prop_default_str, prop_values_str))


@verdi_devel.command('listproperties')
@options.ALL(help='Show all properties, even if not explicitly defined in the configuration file')
def devel_listproperties(all_entries):
    """List all the properties that are explicitly set for the current profile."""
    from aiida.common.setup import _property_table, exists_property, get_property

    for prop in sorted(_property_table.keys()):
        try:
            # To enforce the generation of an exception, even if there is a default value
            if all_entries or exists_property(prop):
                val = get_property(prop)
                echo.echo('{} = {}'.format(prop, val))
        except KeyError:
            pass


@verdi_devel.command('delproperty')
@click.argument('prop', type=click.STRING, metavar='PROPERTY')
def devel_delproperty(prop):
    """Delete the global PROPERTY from the configuration file."""
    from aiida.common.setup import del_property

    try:
        del_property(prop)
    except ValueError:
        echo.echo_critical('property {} not found'.format(prop))
    except Exception as exception:  # pylint: disable=broad-except
        echo.echo_critical('{} while getting the property: {}'.format(type(exception).__name__, exception.message))
    else:
        echo.echo_success('deleted the {} property from the configuration file'.format(prop))


@verdi_devel.command('getproperty')
@click.argument('prop', type=click.STRING, metavar='PROPERTY')
def devel_getproperty(prop):
    """Get the global PROPERTY from the configuration file."""
    from aiida.common.setup import get_property

    try:
        value = get_property(prop)
    except ValueError:
        echo.echo_critical('property {} not found'.format(prop))
    except Exception as exception:  # pylint: disable=broad-except
        echo.echo_critical('{} while getting the property: {}'.format(type(exception).__name__, exception.message))
    else:
        echo.echo('{}'.format(value))


@verdi_devel.command('setproperty')
@click.argument('prop', type=click.STRING, metavar='PROPERTY')
@click.argument('value', type=click.STRING)
def devel_setproperty(prop, value):
    """Set the global PROPERTY to VALUE in the configuration file."""
    from aiida.common.setup import set_property

    try:
        set_property(prop, value)
    except ValueError:
        echo.echo_critical('{} is not a recognized property, call describeproperties to see a list'.format(prop))
    except Exception as exception:  # pylint: disable=broad-except
        echo.echo_critical('{} while storing the property: {}'.format(type(exception).__name__, exception.message))
    else:
        echo.echo_success('property {} set to {}'.format(prop, value))


@verdi_devel.command('run_daemon')
@decorators.with_dbenv()
def devel_run_daemon():
    """Run a daemon instance in the current interpreter."""
    from aiida.daemon.runner import start_daemon
    start_daemon()


@verdi_devel.command('tests')
@click.argument('paths', nargs=-1, type=TestModuleParamType(), required=False)
@options.VERBOSE(help='Print the class and function name for each test.')
@decorators.with_dbenv()
def devel_tests(paths, verbose):  # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    """Run the unittest suite or parts of it."""
    import os
    import sys
    import unittest

    import aiida
    from aiida import settings
    from aiida.backends.testbase import run_aiida_db_tests
    from aiida.backends.testbase import check_if_tests_can_run

    settings.TESTING_MODE = True

    test_failures = []
    test_errors = []
    test_skipped = []
    tot_num_tests = 0
    db_test_list = []
    test_folders = []
    do_db = False

    if paths:
        for path in paths:
            if path in get_valid_test_paths():
                dbtests = get_valid_test_paths()[path]
                # Anything that has been added is a DB test
                if dbtests is not None:
                    do_db = True
                    for dbtest in dbtests:
                        db_test_list.append(dbtest)
                else:
                    test_folders.append(path)
            else:
                valid_tests = '\n'.join('  * {}'.format(a) for a in sorted(get_valid_test_paths().keys()))
                echo.echo_critical('{} is not a valid test, allowed test folders are:\n{}'.format(path, valid_tests))
    else:
        # Without arguments, run all tests
        do_db = True
        for key, value in get_valid_test_paths().iteritems():
            if value is None:
                # Non-db tests
                test_folders.append(key)
            else:
                # DB test
                for dbtest in value:
                    db_test_list.append(dbtest)

    for test_folder in test_folders:
        echo.echo('v' * 75)
        echo.echo('>>> Tests for module {} <<<'.format(test_folder.ljust(50)))
        echo.echo('^' * 75)
        testsuite = unittest.defaultTestLoader.discover(test_folder, top_level_dir=os.path.dirname(aiida.__file__))
        test_runner = unittest.TextTestRunner()
        test_results = test_runner.run(testsuite)
        test_failures.extend(test_results.failures)
        test_errors.extend(test_results.errors)
        test_skipped.extend(test_results.skipped)
        tot_num_tests += test_results.testsRun

    if do_db:
        # Even if each test would fail if we are not in a test profile,
        # it's still better to not even run them in the case the profile
        # is not a test one.
        try:
            check_if_tests_can_run()
        except TestsNotAllowedError as exception:
            echo.echo_critical(exception.message)

        echo.echo('v' * 75)
        echo.echo('>>> Tests for {} db application'.format(settings.BACKEND))
        echo.echo('^' * 75)
        db_results = run_aiida_db_tests(db_test_list, verbose)
        test_skipped.extend(db_results.skipped)
        test_failures.extend(db_results.failures)
        test_errors.extend(db_results.errors)
        tot_num_tests += db_results.testsRun

    echo.echo('Final summary of the run of tests:')
    echo.echo('* Tests skipped: {}'.format(len(test_skipped)))
    if test_skipped:
        echo.echo('  Reasons for skipping:')
        for reason in sorted(set([_[1] for _ in test_skipped])):
            echo.echo('  - {}'.format(reason))

    echo.echo('* Tests run:     {}'.format(tot_num_tests))
    echo.echo('* Tests failed:  {}'.format(len(test_failures)))
    echo.echo('* Tests errored: {}'.format(len(test_errors)))

    # If there was any failure report it with the right exit code
    if test_failures or test_errors:
        sys.exit(len(test_failures) + len(test_errors))


@verdi_devel.command('play')
def devel_play():
    """Open a browser and play the Aida triumphal march by Giuseppe Verdi."""
    import webbrowser

    webbrowser.open_new('http://upload.wikimedia.org/wikipedia/commons/3/32/Triumphal_March_from_Aida.ogg')
