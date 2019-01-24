# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend specific computer objects and methods"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import abc
import six

from aiida.backends.utils import validate_attribute_key
from aiida.common import exceptions
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.lang import type_check
from aiida.orm.implementation.nodes import BackendNode 
from aiida.orm.utils.node import clean_value

__all__ = ('BackendNode', 'BackendNodeCollection', '_NO_DEFAULT')

_NO_DEFAULT = tuple()


# class RepositoryMixin(object):
#     """
#     A mixin class that knows about file repositories, to mix in
#     with the BackendNode class
#     """
#     pass

@six.add_metaclass(abc.ABCMeta)
class BackendProcessNode(BackendNode):
    """
    Backend process node class
    """
    pass