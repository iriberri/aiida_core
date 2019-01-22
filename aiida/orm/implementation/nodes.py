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

from . import backends

__all__ = 'BackendNode', 'BackendNodeCollection'


@six.add_metaclass(abc.ABCMeta)
class BackendNode(backends.BackendEntity):
    """
    Backend node class
    """

    # pylint: disable=too-many-public-methods

    def _init_backend_node(self):
        """
        Initialize internal variables for the backend node
        
        This needs to be called explicitly in each specific
        subclass implementation of the init.
        """
        self._attrs_cache = {}

        # A cache of incoming links represented as a list of LinkTriples instances
        self._incoming_cache = list()

        self._temp_folder = None
        self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

        # TODO: decide what to do with _init_internal_params

    # region db_columns

    @abc.abstractproperty
    def nodeversion(self):
        """
        Get the version number for this node

        :return: the version number
        :rtype: int
        """

    @abc.abstractmethod
    def increment_version_number(self):
        """
        Increment the version number of this node by one
        """

    @abc.abstractproperty
    def uuid(self):
        """
        The node UUID

        :return: the uuid
        """

    @abc.abstractmethod
    def get_computer(self):
        """
        Get the computer associated to the node.
	For a CalcJobNode, this represents the computer on which the calculation was run.
 	However, this can be used also for (some) data nodes, like RemoteData, to indicate
	on which computer the data is sitting.

        :return: the Computer object or None.
        """

    @abc.abstractmethod
    def set_computer(self, computer):
        """
        Set the backend computer

        :param computer: the computer to set for this node
        :type computer: :class:`aiida.orm.implementation.Computer`
        """

    @abc.abstractmethod
    def get_user(self):
        """
        Get the node user

        :return: the node user
        :rtype: :class:`aiida.orm.implementation.User`
        """

    @abc.abstractmethod
    def set_user(self, user):
        """
        Set the node user

        :param user: the new user
        :type user: :class:`aiida.orm.implementation.User`
        """

    @property
    @abc.abstractmethod
    def ctime(self):
        """
        Return the creation time of the node.
        """

    @property
    @abc.abstractmethod
    def mtime(self):
        """
        Return the modification time of the node.
        """

    @property
    @abc.abstractmethod
    def type(self):
        """
        Get the type of the node.

        :return: a string.
        """

    @property
    @abc.abstractmethod
    def nodeversion(self):
        """
        Return the version of the 
        :return: A version integer
        :rtype: int
        """

    @property
    @abc.abstractmethod
    def label(self):
        """
        Get the label of the node.

        :return: a string.
        """

    @label.setter
    @abc.abstractmethod
    def label(self, label):
        """
        Set the label of the node.

        :param label: a string
        """

    @property
    @abc.abstractmethod
    def description(self):
        """
        Get the description of the node.

        :return: a string
        :rtype: str
        """

    @description.setter
    @abc.abstractmethod
    def description(self, description):
        """
        Set the description of the node

        :param desc: a string
        """

    # endregion

    # region Attributes

    def attritems(self):
        """
        Iterator over the attributes, returning tuples (key, value)
        """
        if not self.is_stored:
            for key, value in self._attrs_cache.items():
                yield (key, value)
        else:
            for key, value in self.backend_entity.iterattrs():
                yield key, value

    @abc.abstractmethod
    def attrs(self):
        """
        The attribute keys

        :return: a generator of the keys
        """

    @abc.abstractmethod
    def iterattrs(self):
        """
        Get an iterator to all the attributes

        :return: the attributes iterator
        """

    @abc.abstractmethod
    def get_attrs(self):
        """
        Return a dictionary with all attributes of this node.
        """

    @abc.abstractmethod
    def set_attr(self, key, value):
        """
        Set an attribute on this node

        :param key: key name
        :type key: str
        :param value: the value
        """

    @abc.abstractmethod
    def append_to_attr(self, key, value, clean=True):
        """
        Append value to an attribute of the Node (in the DbAttribute table).

        :param key: key name of "list-type" attribute If attribute doesn't exist, it is created.
        :param value: the value to append to the list
        :param clean: whether to clean the value
            WARNING: when set to False, storing will throw errors
            for any data types not recognized by the db backend
        :raise ValidationError: if the key is not valid, e.g. it contains the separator symbol
        """

    @abc.abstractmethod
    def del_attr(self, key):
        """
        Delete an attribute from this node

        :param key: the attribute key
        :type key: str
        """

    @abc.abstractmethod
    def del_all_attrs(self):
        """
        Delete all attributes associated to this node.

        :raise ModificationNotAllowed: if the Node was already stored.
        """

    # endregion

    # region Extras

    @abc.abstractmethod
    def iterextras(self):
        """
        Get an iterator to the extras

        :return: the extras iterator
        """

    @abc.abstractmethod
    def set_extra(self, key, value, exclusive=False):
        """
        Set an extra on this node

        :param key: the extra key
        :type key: str
        :param value: the extra value
        :param exclusive:
        """

    @abc.abstractmethod
    def get_extra(self, key):
        """
        Get an extra for the node

        :param key: the extra key
        :type key: str
        :return: the extra value
        """

    @abc.abstractmethod
    def del_extra(self, key):
        """
        Delete an extra

        :param key: the extra to delete
        :type key: str
        """

    @abc.abstractmethod
    def reset_extras(self, new_extras):
        """
        Reset all the extras to a new dictionary

        :param new_extras: the dictionary to set the extras to
        :type new_extras: dict
        """

    # endregion

    # region Links

    def has_cached_links(self):
        """
        Return whether there are unstored incoming links in the cache.

        :return: boolean, True when there are links in the incoming cache, False otherwise
        """
        return bool(self._incoming_cache)

    @abc.abstractmethod
    def get_input_links(self, link_type):
        """
        Get the inputs linked by the given link type

        :param link_type: the input links type
        :return: a list of input backend entities
        """

    @abc.abstractmethod
    def get_output_links(self, link_type):
        """
        Get the outputs linked by the given link type

        :param link_type: the output links type
        :return: a list of output backend entities
        """

    @abc.abstractmethod
    def add_link_from(self, src, link_type, label):
        """
        Add an incoming link from a given source node

        :param src: the source node
        :type src: :class:`aiida.orm.implementation.Node`
        :param link_type: the link type
        :param label: the link label
        """

    @abc.abstractmethod
    def remove_link_from(self, label):
        """
        Remove an incoming link with the given label

        :param label: the label of the link to remove
        """

    @abc.abstractmethod
    def replace_link_from(self, src, link_type, label):
        """
        Replace an existing link

        :param src: the source node
        :type src: :class:`aiida.orm.implementation.Node`
        :param link_type: the link type
        :param label: the link label
        """

    # endregion

    # region Comments

    @abc.abstractmethod
    def add_comment(self, content, user=None):
        """
        Add a new comment.

        :param content: string with comment
        :param user: the user to associate with the comment, will use default if not supplied
        :return: the newly created comment
        """

    @abc.abstractmethod
    def get_comment(self, identifier):
        """
        Return a comment corresponding to the given identifier.

        :param identifier: the comment pk
        :raise NotExistent: if the comment with the given id does not exist
        :raise MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        :return: the comment
        """

    @abc.abstractmethod
    def get_comments(self):
        """
        Return a sorted list of comments for this node.

        :return: the list of comments, sorted by pk
        """

    @abc.abstractmethod
    def update_comment(self, identifier, content):
        """
        Update the content of an existing comment.

        :param identifier: the comment pk
        :param content: the new comment content
        :raise NotExistent: if the comment with the given id does not exist
        :raise MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        """

    @abc.abstractmethod
    def remove_comment(self, identifier):
        """
        Delete an existing comment.

        :param identifier: the comment pk
        """

    # endregion

    # region PythonMethods

    def __del__(self):
        """
        Called only upon real object destruction from memory
        I just try to remove junk, whenever possible; do not trust
        too much this function!
        """
        if getattr(self, '_temp_folder', None) is not None:
            self._temp_folder.erase()

    # endregion


@six.add_metaclass(abc.ABCMeta)
class BackendNodeCollection(backends.BackendCollection[BackendNode]):
    """The collection of Node entries."""

    # pylint: disable=too-few-public-methods

    ENTITY_CLASS = BackendNode
