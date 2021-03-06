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
Defines reStructuredText directives to simplify documenting AiiDA and its plugins.
"""

__version__ = '0.1.0'

from . import workchain


def setup(app):
    """
    Setup function to add the extension classes / nodes to Sphinx.
    """
    workchain.setup_aiida_workchain(app)

    return {'version': __version__, 'parallel_read_safe': True}
