# -*- coding: utf-8 -*-
"""Test module parameter type for click."""
import click

from aiida.cmdline.utils.decorators import with_dbenv


class TestModuleParamType(click.ParamType):
    """Parameter type to represent a unittest module."""

    name = 'test module'

    @staticmethod
    def get_test_modules():
        """Returns a list of known test modules."""
        from aiida.backends.tests import get_db_test_names

        prefix_db = 'db'
        modules_db = get_db_test_names()
        modules_base = [
            'aiida.scheduler', 'aiida.transport', 'aiida.common', 'aiida.tests.work', 'aiida.utils', 'aiida.control',
            'aiida.cmdline.tests'
        ]

        test_modules = {}

        for module in modules_base:
            test_modules[module] = None

        for module in modules_db:
            test_modules['{}.{}'.format(prefix_db, module)] = [module]

        test_modules[prefix_db] = modules_db

        return test_modules

    @with_dbenv()
    def convert(self, value, param, ctx):
        return value

    @with_dbenv()
    def complete(self, ctx, incomplete):  # pylint: disable=unused-argument,no-self-use
        """
        Return possible completions based on an incomplete value

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        return [(test_module, '') for test_module in self.get_test_modules() if test_module.startswith(incomplete)]
