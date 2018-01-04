# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.implementation.calculation import Calculation
from aiida.common.exceptions import InvalidOperation
from aiida.common.lang import override
from aiida.common.links import LinkType
# TODO: Replace with local process state (i.e. in AiiDA)
from plum import ProcessState


class WorkCalculation(Calculation):
    """
    Used to represent a calculation generated by a :class:`aiida.work.Process`
    from the workflow system.
    """
    PROCESS_STATE_KEY = 'process_state'
    FINISHED_KEY = '_finished'
    FAILED_KEY = '_failed'
    ABORTED_KEY = '_aborted'
    DO_ABORT_KEY = '_do_abort'

    @override
    def has_finished(self):
        return self.has_finished_ok() or self.has_failed() or self.has_aborted()

    @override
    def has_finished_ok(self):
        """
        Returns True if the work calculation finished normally, False otherwise
        (could be that it's still running)

        :return: True if finished successfully, False otherwise.
        :rtype: bool
        """
        return self.get_attr(self.PROCESS_STATE_KEY) == ProcessState.FINISHED.value

    @override
    def has_failed(self):
        """
        Returns True if the work calculation failed because of an exception,
        False otherwise

        :return: True if the calculation has failed, False otherwise.
        :rtype: bool
        """
        return self.get_attr(self.PROCESS_STATE_KEY) == ProcessState.FAILED.value

    def has_aborted(self):
        """
        Returns True if the work calculation was killed and is

        :return: True if the calculation was killed, False otherwise.
        :rtype: bool
        """
        return self.get_attr(self.PROCESS_STATE_KEY) == ProcessState.CANCELLED.value

    def kill(self):
        """
        Kill a WorkCalculation and all its children.
        """
        from aiida.orm.calculation.job import JobCalculation
        from aiida.common.exceptions import InvalidOperation

        if not self.is_sealed:
            self._set_attr(self.DO_ABORT_KEY, 'killed by user')

        for child in self.get_outputs(link_type=LinkType.CALL):
            try:
                child.kill()
            except InvalidOperation as e:
                if isinstance(child, JobCalculation):
                    # Cannot kill calculations that are already killed: skip and go to the next step
                    pass
                else:
                    raise