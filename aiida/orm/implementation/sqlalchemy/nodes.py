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

from aiida.backends.sqlalchemy.models import node as models
from aiida.backends.sqlalchemy import get_scoped_session

from .. import BackendNode, BackendNodeCollection
from . import entities
from . import utils


class SqlaNode(entities.SqlaModelEntity[models.DbNode], BackendNode):
    """SQLA Node backend entity"""

    MODEL_CLASS = models.DbNode
    EXTRA_CLASS = models.DbExtra


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

    def _increment_version_number(self):
        """
        Increment the node version number of this node by one
        directly in the database
        """
        self._dbmodel.nodeversion = self.nodeversion + 1
        try:
            self._dbmodel.save()
        except:
            session = get_scoped_session()
            session.rollback()
            raise

    def _ensure_model_uptodate(self, attribute_names=None):
        """
        Expire specific fields of the dbmodel (or, if attribute_names
        is not specified, all of them), so they will be re-fetched
        from the DB.

        :param attribute_names: by default, expire all columns.
             If you want to expire only specific columns, pass
             a list of strings with the column names.
        """
        if self.is_stored:
            self._dbmodel.session.expire(self._dbmodel, attribute_names=attribute_names)

    def _attributes(self):
        """
        Return the attributes, ensuring first that the model 
        is up to date.
        """
        self._ensure_model_uptodate(['attributes'])
        return self._dbmodel.attributes

    def _extras(self):
        """
        Return the extras, ensuring first that the model 
        is up to date.
        """
        self._ensure_model_uptodate(['extras'])
        return self._dbmodel.extras

    def _get_db_attrs_items(self):
        """
        Iterator over the attributes, returning tuples (key, value),
        that actually performs the job directly on the DB.

        :return: a generator of the (key, value) pairs
        """
        for key, val in self._attributes().items():
            yield (key, val)

    def _get_db_attrs_keys(self):
        """
        Iterator over the attributes, returning the attribute keys only,
        that actually performs the job directly on the DB.

        Note: It is independent of the _get_db_attrs_items
        because it is typically faster to retrieve only the keys
        from the database, especially if the values are big.    

        :return: a generator of the keys
        """
        for key in self._attributes().keys():
            yield key

    def _set_db_attr(self, key, value):
        """
        Set the value directly in the DB, without checking if it is stored, or
        using the cache.

        :param key: key name
        :param value: its value
        """
        try:
            self._dbmodel.set_attr(key, value)
        except Exception:
            session = get_scoped_session()
            session.rollback()
            raise

    def _del_db_attr(self, key):
        """
        Delete an attribute directly from the DB

        :param key: The key of the attribute to delete
        """
        try:
            self._dbmodel.del_attr(key)
        except Exception:
            session = get_scoped_session()
            session.rollback()
            raise

    def _get_db_attr(self, key):
        """
        Return the attribute value, directly from the DB.

        :param key: the attribute key
        :return: the attribute value
        :raise AttributeError: if the attribute does not exist.
        """
        try:
            return utils.get_attr(self._attributes(), key)
        except (KeyError, IndexError):
            raise AttributeError("Attribute '{}' does not exist".format(key))

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

    def nodeversion(self):
        """
        Get the version number for this node

        :return: the version number
        :rtype: int
        """
        self._ensure_model_uptodate(attribute_names=['nodeversion'])
        return self._dbmodel.nodeversion

    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        self._ensure_model_uptodate(attribute_names=['ctime'])
        return self._dbmodel.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        self._ensure_model_uptodate(attribute_names=['mtime'])
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
        if exclusive:
            raise NotImplementedError("exclusive=True not implemented yet in SQLAlchemy backend")

        try:
            self._dbmodel.set_extra(key, value)
        except Exception:
            session = get_scoped_session()
            session.rollback()
            raise

    def _reset_db_extras(self, new_extras):
        """
        Resets the extras (replacing existing ones) directly in the DB

        DO NOT USE DIRECTLY!

        :param new_extras: dictionary with new extras
        """
        try:
            self._dbmodel.reset_extras(new_extras)
        except Exception:
            session = get_scoped_session()
            session.rollback()
            raise

    def _get_db_extra(self, key):
        """
        Get an extra, directly from the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        :return: the key value
        :raise AttributeError: if the key does not exist
        """ 
        try:
            return utils.get_attr(self._extras(), key)
        except (KeyError, AttributeError):
            raise AttributeError("DbExtra {} does not exist".format(key))

    def _del_db_extra(self, key):
        """
        Delete an extra, directly on the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        """
        try:
            self._dbmodel.del_extra(key)
        except:
            session = get_scoped_session()
            session.rollback()
            raise

    def _db_extras_items(self):
        """
        Iterator over the extras (directly in the DB!)

        DO NOT USE DIRECTLY.
        """
        extras = self._extras()
        if extras is None:
            return iter(dict().items())

        return iter(extras.items())


class SqlaNodeCollection(BackendNodeCollection):
    """The SQLA collection for nodes"""

    ENTITY_CLASS = SqlaNode
