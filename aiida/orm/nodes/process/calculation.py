# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for Node entities"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import importlib
import os
import typing
import warnings

import six

from aiida.orm.utils import links
from aiida.backends.utils import validate_attribute_key
from aiida.common.hashing import _HASH_EXTRA_KEY
from aiida.common.links import LinkType
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
from aiida.common import exceptions
from aiida.common.lang import combomethod, classproperty, type_check
from aiida.common.escaping import sql_string_match
from aiida.manage import get_manager
from aiida.manage.caching import get_use_cache
from aiida.orm.nodes.process import ProcessNode
from aiida.orm.utils.node import AbstractNodeMeta
from aiida.orm.utils.managers import NodeInputManager, NodeOutputManager
from aiida.orm.implementation.nodes import _NO_DEFAULT
from . import comments
from . import convert
from . import entities
from . import groups
from . import computers
from . import querybuilder
from . import users

__all__ = ('Node',)

@six.add_metaclass(AbstractNodeMeta)
class CalculationNode(ProcessNode):
    """
    Base frontend class for calculation nodes in AiiDA.
     
    TODO: Document
    """
    pass