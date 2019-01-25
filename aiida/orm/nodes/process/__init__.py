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
from aiida.orm.nodes import Node
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
class ProcessNode(Node):
    """
    Base frontend class for process nodes in AiiDA.
     
    TODO: Document
    """

    @property
    def logger(self):
        """
        Get the logger of the Calculation object, so that it also logs to the DB.

        :return: LoggerAdapter object, that works like a logger, but also has the 'extra' embedded
        """
        return self._backend_entity.logger()
    
    @property
    def process_label(self):
        """
        Return the process label

        :returns: the process label
        """
        return self._backend_entity.process_label()

    @property
    def process_state(self):
        """
        Return the process state

        :returns: the process state instance of ProcessState enum
        """
        return self._backend_entity.process_state()

    @property
    def process_status(self):
        """
        Return the process status

        The process status is a generic status message e.g. the reason it might be paused or when it is being killed

        :returns: the process status
        """
        return self._backend_entity.process_status()

    @property
    def is_terminated(self):
        """
        Return whether the process has terminated

        Terminated means that the process has reached any terminal state.

        :return: True if the process has terminated, False otherwise
        :rtype: bool
        """
        return self._backend_entity.is_terminated()

    @property
    def is_excepted(self):
        """
        Return whether the process has excepted

        Excepted means that during execution of the process, an exception was raised that was not caught.

        :return: True if during execution of the process an exception occurred, False otherwise
        :rtype: bool
        """
        return self._backend_entity.is_excepted()

    @property
    def is_killed(self):
        """
        Return whether the process was killed

        Killed means the process was killed directly by the user or by the calling process being killed.

        :return: True if the process was killed, False otherwise
        :rtype: bool
        """
        return self._backend_entity.is_killed()


    @property
    def is_finished(self):
        """
        Return whether the process has finished

        Finished means that the process reached a terminal state nominally.
        Note that this does not necessarily mean successfully, but there were no exceptions and it was not killed.

        :return: True if the process has finished, False otherwise
        :rtype: bool
        """
        return self._backend_entity.is_finished()

    @property
    def is_finished_ok(self):
        """
        Return whether the process has finished successfully

        Finished successfully means that it terminated nominally and had a zero exit status.

        :return: True if the process has finished successfully, False otherwise
        :rtype: bool
        """
        return self._backend_entity.is_finished_ok()

    @property
    def is_failed(self):
        """
        Return whether the process has failed

        Failed means that the process terminated nominally but it had a non-zero exit status.

        :return: True if the process has failed, False otherwise
        :rtype: bool
        """
        return self._backend_entity.is_failed()

    @property
    def exit_status(self):
        """
        Return the exit status of the process

        :returns: the exit status, an integer exit code or None
        """
        return self._backend_entity.exit_status()

    @property
    def exit_message(self):
        """
        Return the exit message of the process

        :returns: the exit message
        """
        return self._backend_entity.exit_message()

    @property
    def exception(self):
        """
        Return the exception of the process or None if the process is not excepted.

        If the process is marked as excepted yet there is no exception attribute, an empty string will be returned.

        :returns: the exception message or None
        """
        return self._backend_entity.exception()

    @property
    def checkpoint(self):
        """
        Return the checkpoint bundle set for the process

        :returns: checkpoint bundle if it exists, None otherwise
        """
        return self._backend_entity.checkpoint()

    @property
    def paused(self):
        """
        Return whether the process is paused

        :returns: True if the Calculation is marked as paused, False otherwise
        """
        return self._backend_entity.paused()
    
    @property
    def called(self):
        """
        Return a list of nodes that the process called

        :returns: list of process nodes called by this process
        """
        return self._backend_entity.called()

    @property
    def called_descendants(self):
        """
        Return a list of all nodes that have been called downstream of this process

        This will recursively find all the called processes for this process and its children.
        """
        return self._backend_entity.called_descendants()

    @property
    def called_by(self):
        """
        Return the process node that called this process node, or None if it does not have a caller

        :returns: process node that called this process node instance or None
        """
        return self._backend_entity.called_by()