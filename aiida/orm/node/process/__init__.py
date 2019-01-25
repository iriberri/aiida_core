# -*- coding: utf-8 -*-
# pylint: disable=wildcard-import,cyclic-import,no-self-argument
"""Package for process node ORM classes."""
from __future__ import absolute_import

import enum
import six

from plumpy import ProcessState

from aiida.common.links import LinkType
from aiida.common.lang import classproperty
from aiida.orm.implementation import Node
from aiida.orm.mixins import Sealable
from aiida.plugins.entry_point import get_entry_point_string_from_class


class ProcessNode(Sealable, Node):
    """
    Base class for all nodes representing the execution of a process

    This class and its subclasses serve as proxies in the database, for actual `Process` instances being run. The
    `Process` instance in memory will leverage an instance of this class (the exact sub class depends on the sub class
    of `Process`) to persist important information of its state to the database. This serves as a way for the user to
    inspect the state of the `Process` during its execution as well as a permanent record of its execution in the
    provenance graph, after the execution has terminated.
    """
    # pylint: disable=too-many-public-methods,abstract-method

    CHECKPOINT_KEY = 'checkpoints'
    EXCEPTION_KEY = 'exception'
    EXIT_MESSAGE_KEY = 'exit_message'
    EXIT_STATUS_KEY = 'exit_status'
    PROCESS_PAUSED_KEY = 'paused'
    PROCESS_LABEL_KEY = 'process_label'
    PROCESS_STATE_KEY = 'process_state'
    PROCESS_STATUS_KEY = 'process_status'

    # The link_type might not be correct while the object is being created.
    _hash_ignored_inputs = ['CALL_CALC', 'CALL_WORK']

    # Specific sub classes should be marked as cacheable when appropriate
    _cacheable = False

    _unstorable_message = 'only Data, WorkflowNode, CalculationNode or their subclasses can be stored'

    def __str__(self):
        base = super(ProcessNode, self).__str__()
        if self.process_type:
            return '{} ({})'.format(base, self.process_type)

        return '{}'.format(base)

    @classproperty
    def _updatable_attributes(cls):
        return super(ProcessNode, cls)._updatable_attributes + (
            cls.PROCESS_PAUSED_KEY,
            cls.CHECKPOINT_KEY,
            cls.EXCEPTION_KEY,
            cls.EXIT_MESSAGE_KEY,
            cls.EXIT_STATUS_KEY,
            cls.PROCESS_LABEL_KEY,
            cls.PROCESS_STATE_KEY,
            cls.PROCESS_STATUS_KEY,
        )

    

    

    
    

    
    

    