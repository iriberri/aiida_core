# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.sqlalchemy.models import node as models

from .. import BackendNode, BackendNodeCollection
from . import entities
from . import utils


class SqlaNode(entities.SqlaModelEntity[models.DbNode], BackendNode):
    """SQLA Node backend entity"""

    MODEL_CLASS = models.DbNode

    # TODO: check how many parameters we want to expose in the init
    # and if we need to define here some defaults
    def __init__(self, backend, type, process_type, label, description):
        super(SqlaNode, self).__init__(backend)
        self._dbmodel = utils.ModelWrapper(
            models.DbNode(
                type=type,
                process_type=process_type,
                label=label,
                description=description,
            ))
        self._init_backend_node()

    @property
    def uuid(self):
        """
        Get the UUID of the log entry
        """
        return self._dbmodel.uuid


class SqlaNodeCollection(BackendNodeCollection):
    """The SQLA collection for nodes"""

    ENTITY_CLASS = SqlaNode
