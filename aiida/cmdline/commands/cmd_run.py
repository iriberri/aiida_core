# -*- coding: utf-8 -*-
"""`verdi run` command."""
import contextlib
import os
import sys

import click

from aiida.cmdline.commands import verdi
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.utils import decorators, echo


@contextlib.contextmanager
def update_environment(new_argv):
    """
    Used as a context manager, changes sys.argv with the
    new_argv argument, and restores it upon exit.
    """
    import sys

    _argv = sys.argv[:]
    sys.argv = new_argv[:]
    yield

    # Restore old parameters when exiting from the context manager
    sys.argv = _argv


@verdi.command('run', context_settings=dict(ignore_unknown_options=True,))
@click.argument('scriptname', type=click.STRING)
@click.argument('varargs', nargs=-1, type=click.UNPROCESSED)
@click.option('-g', '--group', is_flag=True, default=True, show_default=True, help='Enables the autogrouping')
@click.option('-n', '--group-name', type=click.STRING, required=False, help='Specify the name of the auto group')
@click.option('-e', '--exclude', cls=MultipleValueOption, default=[], help='Exclude these classes from auto grouping')
@click.option('-i', '--include', cls=MultipleValueOption, default=['all'], help='Include these classes from auto grouping')
@click.option(
    '-E',
    '--excludesubclasses',
    cls=MultipleValueOption, default=[],
    help='Exclude these classes and their sub classes from auto grouping')
@click.option(
    '-I',
    '--includesubclasses',
    cls=MultipleValueOption, default=[],
    help='Include these classes and their sub classes from auto grouping')
@decorators.with_dbenv()
def run(scriptname, varargs, group, group_name, exclude, excludesubclasses, include, includesubclasses):
    """Execute an AiiDA script."""
    from aiida.cmdline.commands.cmd_shell import DEFAULT_MODULES_LIST
    from aiida.orm import autogroup

    # Prepare the environment for the script to be run
    globals_dict = {
        '__builtins__': globals()['__builtins__'],
        '__name__': '__main__',
        '__file__': scriptname,
        '__doc__': None,
        '__package__': None
    }

    # Dynamically load modules (the same of verdi shell) - but in globals_dict, not in the current environment
    for app_mod, model_name, alias in DEFAULT_MODULES_LIST:
        globals_dict['{}'.format(alias)] = getattr(__import__(app_mod, {}, {}, model_name), model_name)

    if group:
        automatic_group_name = group_name
        if automatic_group_name is None:
            from aiida.utils import timezone

            now = timezone.now()
            automatic_group_name = 'Verdi autogroup on ' + now.strftime("%Y-%m-%d %H:%M:%S")

        aiida_verdilib_autogroup = autogroup.Autogroup()
        aiida_verdilib_autogroup.set_exclude(exclude)
        aiida_verdilib_autogroup.set_include(include)
        aiida_verdilib_autogroup.set_exclude_with_subclasses(excludesubclasses)
        aiida_verdilib_autogroup.set_include_with_subclasses(includesubclasses)
        aiida_verdilib_autogroup.set_group_name(automatic_group_name)

        # Note: this is also set in the exec environment! This is the intended behavior
        autogroup.current_autogroup = aiida_verdilib_autogroup

    try:
        f = open(scriptname)
    except IOError:
        echo.echo_critical("{}: Unable to load file '{}'".format(self.get_full_command_name(), scriptname))
    else:
        try:
            # Must add also argv[0]
            new_argv = [scriptname] + list(varargs)
            with update_environment(new_argv=new_argv):
                # Add local folder to sys.path
                sys.path.insert(0, os.path.abspath(os.curdir))
                # Pass only globals_dict
                exec (f, globals_dict)
        except SystemExit as e:
            # Script called sys.exit()
            # Re-raise the exception to have the error code properly returned at the end
            raise
        finally:
            f.close()
