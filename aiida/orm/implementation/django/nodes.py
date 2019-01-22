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

import six

from aiida.backends.djsite.db import models

from .. import BackendNode, BackendNodeCollection
from . import entities


class DjangoNode(entities.SqlaModelEntity[models.DbNode], BackendNode):
    """Django Node backend entity"""

    MODEL_CLASS = models.DbNode
    ATTRIBUTE_CLASS = models.DbAttribute
    EXTRA_CLASS = models.DbExtra

    # TODO: check how many parameters we want to expose in the init
    # and if we need to define here some defaults
    def __init__(self, backend, type, process_type, label, description):
        # pylint: disable=too-many-arguments
        super(DjangoNode, self).__init__(backend)
        self._dbmodel = models.DbNode(
            type=type,
            process_type=process_type,
            label=label,
            description=description,
        )
        self._init_backend_node()

    def _increment_version_number(self):
        """
        Increment the node version number of this node by one
        directly in the database
        """
        from django.db.models import F

        # I increment the node number using a filter
        self._dbmodel.nodeversion = F('nodeversion') + 1
        self._dbmodel.save()

        # This reload internally the node of self._dbmodel
        # Note: I have to reload the object (to have the right values in memory),
        # otherwise I only get the Django Field F object as a result!
        self._dbmodel = self.MODEL_CLASS.objects.get(pk=self._dbmodel.pk)

    def _get_db_attrs_items(self):
        """
        Iterator over the attributes, returning tuples (key, value),
        that actually performs the job directly on the DB.

        :return: a generator of the (key, value) pairs
        """
        all_attrs = self.ATTRIBUTE_CLASS.get_all_values_for_node(self._dbmodel)
        for attr in all_attrs:
            yield (attr, all_attrs[attr])

    def _get_db_attrs_keys(self):
        """
        Iterator over the attributes, returning the attribute keys only,
        that actually performs the job directly on the DB.

        Note: It is independent of the _get_db_attrs_items
        because it is typically faster to retrieve only the keys
        from the database, especially if the values are big.    

        :return: a generator of the keys
        """
        attrlist = self.ATTRIBUTE_CLASS.list_all_node_elements(self._dbmodel)
        for attr in attrlist:
            yield attr.key   

    def _set_db_attr(self, key, value):
        """
        Set the value directly in the DB, without checking if it is stored, or
        using the cache.

        :param key: key name
        :param value: its value
        """
        self.ATTRIBUTE_CLASS.set_value_for_node(self._dbmodel, key, value)

    def _del_db_attr(self, key):
        """
        Delete an attribute directly from the DB

        :param key: The key of the attribute to delete
        """
        if not self.ATTRIBUTE_CLASS.has_key(self._dbmodel, key):
            raise AttributeError("DbAttribute {} does not exist".format(key))
        self.ATTRIBUTE_CLASS.del_value_for_node(self._dbmodel, key)

    def _get_db_attr(self, key):
        """
        Return the attribute value, directly from the DB.

        :param key: the attribute key
        :return: the attribute value
        :raise AttributeError: if the attribute does not exist.
        """
        return self.ATTRIBUTE_CLASS.get_value_for_node(dbnode=self._dbmodel, key=key)

    @property
    def uuid(self):
        """
        Get the UUID of the log entry
        """
        return six.text_type(self._dbmodel.uuid)

    def process_type(self):
        """
        The node process_type

        :return: the process type
        """
        return self._dbmodel.process_type

    def nodeversion(self):
        """
        Get the version number for this node

        :return: the version number
        :rtype: int
        """
        return self._dbmodel.nodeversion

    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        return self._dbmodel.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        return self._dbmodel.mtime

    def _set_db_extra(self, key, value, exclusive=False):        
        """
        Store extra directly in the DB, without checks.

        DO NOT USE DIRECTLY.

        :param key: key name
        :param value: key value
        :param exclusive: (default=False).
            If exclusive is True, it raises a UniquenessError if an Extra with
            the same name already exists in the DB (useful e.g. to "lock" a
            node and avoid to run multiple times the same computation on it).
        """
        self.EXTRA_CLASS.set_value_for_node(self._dbmodel, key, value, stop_if_existing=exclusive)

    def _reset_db_extras(self, new_extras):
                """
        Resets the extras (replacing existing ones) directly in the DB

        DO NOT USE DIRECTLY!

        :param new_extras: dictionary with new extras
        """
        raise NotImplementedError("Reset of extras has not been implemented" "for Django backend.")
    
    def _get_db_extra(self, key):
        """
        Get an extra, directly from the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        :return: the key value
        :raise AttributeError: if the key does not exist
        """        
        return self.EXTRA_CLASS.get_value_for_node(dbnode=self._dbmodel, key=key)
    
    def _del_db_extra(self, key):
        """
        Delete an extra, directly on the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        """
        if not self.EXTRA_CLASS.has_key(self._dbmodel, key):
            raise AttributeError("DbExtra {} does not exist".format(key))
        return self.EXTRA_CLASS.del_value_for_node(self._dbmodel, key)

    def _db_extras_items(self):
        """
        Iterator over the extras (directly in the DB!)

        DO NOT USE DIRECTLY.
        """
        extraslist = self.EXTRA_CLASS.list_all_node_elements(self._dbmodel)
        for e in extraslist:
            yield (e.key, e.getvalue())

class DjangoNodeCollection(BackendNodeCollection):
    """The Django collection for nodes"""

    ENTITY_CLASS = DjangoNode
