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
from abc import ABCMeta, abstractmethod, abstractproperty

import os
import logging
import importlib
from collections import Callable, Iterable, Mapping
import numbers
import math
import warnings

import six

from aiida.backends.utils import validate_attribute_key
from aiida.manage.caching import get_use_cache
from aiida.common.exceptions import InternalError, ModificationNotAllowed, UniquenessError, ValidationError, \
    InvalidOperation, StoringNotAllowed
from aiida.common.folders import SandboxFolder
from aiida.common.hashing import _HASH_EXTRA_KEY
from aiida.common.links import LinkType
from aiida.common.lang import override, abstractclassmethod, combomethod, classproperty
from aiida.common.escaping import sql_string_match
from aiida.manage import get_manager
from aiida.orm.utils import links
from aiida.orm.utils.node import get_type_string_from_class, get_query_type_from_type_string


@six.add_metaclass(_AbstractNodeMeta)
class AbstractNode(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything
    only on store(). After the call to store(), attributes cannot be changed.

    Only after storing (or upon loading from uuid) extras can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in
    the 'type' field.
    """

    # Name to be used for the Repository section
    _section_name = 'node'

    # The name of the subfolder in which to put the files/directories
    # added with add_path
    _path_subfolder_name = 'path'

    # A list of tuples, saying which attributes cannot be set at the same time
    # See documentation in the set() method.
    _set_incompatibilities = []

    # A tuple of attribute names that can be updated even after node is stored
    # Requires Sealable mixin, but needs empty tuple for base class
    _updatable_attributes = tuple()

    # A tuple of attribute names that will be ignored when creating the hash.
    _hash_ignored_attributes = tuple()

    # Flag that determines whether the class can be cached.
    _cacheable = True

    # Flag that says if the node is storable or not.
    # By default, bare nodes (and also ProcessNodes) are not storable,
    # all subclasses (WorkflowNode, CalculationNode, Data and their subclasses)
    # are storable. This flag is checked in store()
    _storable = False
    _unstorable_message = 'only Data, WorkflowNode, CalculationNode or their subclasses can be stored'


    @abstractmethod
    def __init__(self, **kwargs):
        """
        Initialize the object Node.

        :param uuid: if present, the Node with given uuid is
          loaded from the database.
          (It is not possible to assign a uuid to a new Node.)
        """
        self._to_be_stored = True

        # A cache of incoming links represented as a list of LinkTriples instances
        self._incoming_cache = list()

        self._temp_folder = None
        self._repo_folder = None

        self._backend = get_manager().get_backend()

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if not self.is_stored:
            return "uuid: {} (unstored)".format(self.uuid)

        return "uuid: {} (pk: {})".format(self.uuid, self.pk)

    def __copy__(self):
        """Copying a Node is not supported in general, but only for the Data sub class."""
        raise InvalidOperation('copying a base Node is not supported')

    def __deepcopy__(self, memo):
        """Deep copying a Node is not supported in general, but only for the Data sub class."""
        raise InvalidOperation('deep copying a base Node is not supported')


    def _init_internal_params(self):
        """
        Set the default values for this class; this method is automatically called by the init.

        :note: if you inherit this function, ALWAYS remember to
          call super()._init_internal_params() as the first thing
          in your inherited function.
        """
        pass

    @property
    def _set_defaults(self):
        """
        Default values to set in the __init__, if no value is explicitly provided
        for the given key.
        It is a dictionary, with k=v; if the key k is not provided to the __init__,
        and a value is present here, this is set.
        """
        return {}

    @abstractclassmethod
    def query(cls, *args, **kwargs):
        """
        Map to the aiidaobjects manager of the DbNode, that returns
        Node objects (or their subclasses) instead of DbNode entities.

        # TODO: VERY IMPORTANT: the recognition of a subclass from the type
        #       does not work if the modules defining the subclasses are not
        #       put in subfolders.
        #       In the future, fix it either to make a cache and to store the
        #       full dependency tree, or save also the path.
        """
        pass

    def _set_with_defaults(self, **kwargs):
        """
        Calls the set() method, but also adds the class-defined default
        values (defined in the self._set_defaults attribute),
        if they are not provided by the user.

        :note: for the default values, also allow to define 'hidden' methods,
            meaning that if a default value has a key "_state", it will not call
            the function "set__state" but rather "_set_state".
            This is not allowed, instead, for the standard set() method.
        """
        self._set_internal(arguments=self._set_defaults, allow_hidden=True)

        # Pass everything to 'set'
        self.set(**kwargs)

    def set(self, **kwargs):
        """
        For each k=v pair passed as kwargs, call the corresponding
        set_k(v) method (e.g., calling self.set(property=5, mass=2) will
        call self.set_property(5) and self.set_mass(2).
        Useful especially in the __init__.

        :note: it uses the _set_incompatibilities list of the class to check
            that we are not setting methods that cannot be set at the same time.
            _set_incompatibilities must be a list of tuples, and each tuple
            specifies the elements that cannot be set at the same time.
            For instance, if _set_incompatibilities = [('property', 'mass')],
            then the call self.set(property=5, mass=2) will raise a ValueError.
            If a tuple has more than two values, it raises ValueError if *all*
            keys are provided at the same time, but it does not give any error
            if at least one of the keys is not present.

        :note: If one element of _set_incompatibilities is a tuple with only
            one element, this element will not be settable using this function
            (and in particular,

        :raise ValueError: if the corresponding set_k method does not exist
            in self, or if the methods cannot be set at the same time.
        """
        self._set_internal(arguments=kwargs, allow_hidden=False)

    def _set_internal(self, arguments, allow_hidden=False):
        """
        Works as self.set(), but takes a dictionary as the 'arguments' variable,
        instead of reading it from the ``kwargs``; moreover, it allows to specify
        allow_hidden to True. In this case, if a a key starts with and
        underscore, as for instance ``_state``, it will not call
        the function ``set__state`` but rather ``_set_state``.
        """
        for incomp in self._set_incompatibilities:
            if all(k in arguments.keys() for k in incomp):
                if len(incomp) == 1:
                    raise ValueError("Cannot set {} directly when creating "
                                     "the node or using the .set() method; "
                                     "use the specific method instead.".format(incomp[0]))
                else:
                    raise ValueError("Cannot set {} at the same time".format(" and ".join(incomp)))

        for k, v in arguments.items():
            try:
                if allow_hidden and k.startswith("_"):
                    method = getattr(self, '_set_{}'.format(k[1:]))
                else:
                    method = getattr(self, 'set_{}'.format(k))
            except AttributeError:
                raise ValueError("Unable to set '{0}', no set_{0} method " "found".format(k))
            if not isinstance(method, Callable):
                raise ValueError("Unable to set '{0}', set_{0} is not " "callable!".format(k))
            method(v)



    @abstractproperty
    def nodeversion(self):
        """
        Return the version of the node

        :return: A version integer
        """
        pass

    @property
    def label(self):
        """
        Get the label of the node.

        :return: a string.
        """
        return self._get_db_label_field()

    @label.setter
    def label(self, label):
        """
        Set the label of the node.

        :param label: a string
        """
        self._update_db_label_field(label)

    @abstractmethod
    def _get_db_label_field(self):
        """
        Get the label field acting directly on the DB

        :return: a string.
        """
        pass

    @abstractmethod
    def _update_db_label_field(self, field_value):
        """
        Set the label field acting directly on the DB
        """
        pass

    @property
    def description(self):
        """
        Get the description of the node.

        :return: a string
        :rtype: str
        """
        return self._get_db_description_field()

    @description.setter
    def description(self, desc):
        """
        Set the description of the node

        :param desc: a string
        """
        self._update_db_description_field(desc)

    @abstractmethod
    def _get_db_description_field(self):
        """
        Get the description of this node, acting directly at the DB level
        """
        pass

    @abstractmethod
    def _update_db_description_field(self, field_value):
        """
        Update the description of this node, acting directly at the DB level
        """
        pass

    def _validate(self):
        """
        Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr
        and similar methods that automatically read either from the DB or
        from the internal attribute cache.

        For the base class, this is always valid. Subclasses will
        reimplement this.
        In the subclass, always call the super()._validate() method first!
        """
        return True

    @property
    def _repository_folder(self):
        """
        Get the permanent repository folder.
        Use preferentially the folder property.

        :return: the permanent RepositoryFolder object
        """
        return self._repo_folder

    @property
    def folder(self):
        """
        Get the folder associated with the node,
        whether it is in the temporary or the permanent repository.

        :return: the RepositoryFolder object.
        """
        if not self.is_stored:
            return self._get_temp_folder()
        else:
            return self._repository_folder

    @property
    def _get_folder_pathsubfolder(self):
        """
        Get the subfolder in the repository.

        :return: a Folder object.
        """
        return self.folder.get_subfolder(self._path_subfolder_name, reset_limit=True)

    def get_folder_list(self, subfolder='.'):
        """
        Get the the list of files/directory in the repository of the object.

        :param subfolder: get the list of a subfolder
        :return: a list of strings.
        """
        return self._get_folder_pathsubfolder.get_subfolder(subfolder).get_content_list()

    def _get_temp_folder(self):
        """
        Get the folder of the Node in the temporary repository.

        :return: a SandboxFolder object mapping the node in the repository.
        """
        # I create the temp folder only at is first usage
        if self._temp_folder is None:
            self._temp_folder = SandboxFolder()  # This is also created
            # Create the 'path' subfolder in the Sandbox
            self._get_folder_pathsubfolder.create()
        return self._temp_folder

    def remove_path(self, path):
        """
        Remove a file or directory from the repository directory.
        Can be called only before storing.

        :param str path: relative path to file/directory.
        """
        if self.is_stored:
            raise ModificationNotAllowed("Cannot delete a path after storing the node")

        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path " "must be a relative path")
        self._get_folder_pathsubfolder.remove_path(path)

    def add_path(self, src_abs, dst_path):
        """
        Copy a file or folder from a local file inside the repository directory.
        If there is a subpath, folders will be created.

        Copy to a cache directory if the entry has not been saved yet.

        :param str src_abs: the absolute path of the file to copy.
        :param str dst_filename: the (relative) path on which to copy.

        :todo: in the future, add an add_attachment() that has the same
            meaning of a extras file. Decide also how to store. If in two
            separate subfolders, remember to reset the limit.
        """
        if self.is_stored:
            raise ModificationNotAllowed("Cannot insert a path after storing the node")

        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a" "filename without any subfolder")
        self._get_folder_pathsubfolder.insert_path(src_abs, dst_path)

    def get_abs_path(self, path=None, section=None):
        """
        Get the absolute path to the folder associated with the
        Node in the AiiDA repository.

        :param str path: the name of the subfolder inside the section. If None
                         returns the abspath of the folder. Default = None.
        :param section: the name of the subfolder ('path' by default).
        :return: a string with the absolute path

        For the moment works only for one kind of files, 'path' (internal files)
        """
        if path is None:
            return self.folder.abspath
        if section is None:
            section = self._path_subfolder_name
        # TODO: For the moment works only for one kind of files,
        #      'path' (internal files)
        if os.path.isabs(path):
            raise ValueError("The path in get_abs_path must be relative")
        return self.folder.get_subfolder(section, reset_limit=True).get_abs_path(path, check_existence=True)

    def store_all(self, with_transaction=True, use_cache=None):
        """
        Store the node, together with all input links.

        Unstored nodes from cached incoming linkswill also be stored.

        :parameter with_transaction: if False, no transaction is used. This is meant to be used ONLY if the outer
            calling function has already a transaction open!
        """
        if self.is_stored:
            raise ModificationNotAllowed('Node<{}> is already stored'.format(self.id))

        # For each node of a cached incoming link, check that all its incoming links are stored
        for link_triple in self._incoming_cache:
            try:
                link_triple.node._check_are_parents_stored()
            except ModificationNotAllowed:
                raise ModificationNotAllowed(
                    'source Node<{}> has unstored parents, cannot proceed (only direct parents can be unstored and '
                    'will be stored by store_all, not grandparents or other ancestors'.format(link_triple.node.pk))

        return self._db_store_all(with_transaction, use_cache=use_cache)

    @abstractmethod
    def _db_store_all(self, with_transaction=True, use_cache=None):
        """
        Store the node, together with all input links, if cached, and also the
        linked nodes, if they were not stored yet.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!

        :param use_cache: Determines whether caching is used to find an equivalent node.
        :type use_cache: bool
        """
        pass

    def _store_input_nodes(self):
        """
        Find all input nodes, and store them, checking that they do not
        have unstored inputs in turn.

        :note: this function stores all nodes without transactions; always
          call it from within a transaction!
        """
        if self.is_stored:
            raise ModificationNotAllowed('Node<{}> is already stored, but this method can only be called for '
                                         'unstored nodes'.format(self.pk))

        for link_triple in self._incoming_cache:
            if not link_triple.node.is_stored:
                link_triple.node.store(with_transaction=False)

    def _check_are_parents_stored(self):
        """
        Check if all parents are already stored, otherwise raise.

        :raise ModificationNotAllowed: if one of the input nodes is not already stored.
        """
        for link_triple in self._incoming_cache:
            if not link_triple.node.is_stored:
                raise ModificationNotAllowed(
                    "Cannot store the incoming link triple {} because the source node is not stored. Either store it "
                    "first, or call _store_input_links with `store_parents` set to True".format(link_triple.link_label))

    @abstractmethod
    def _store_cached_input_links(self, with_transaction=True):
        """
        Store all input links that are in the local cache, transferring them
        to the DB.

        :note: This can be called only if all parents are already stored.

        :note: Links are stored only after the input nodes are stored. Moreover,
            link storage is done in a transaction, and if one of the links
            cannot be stored, an exception is raised and *all* links will remain
            in the cache.

        :note: This function can be called only after the node is stored.
           After that, it can be called multiple times, and nothing will be
           executed if no links are still in the cache.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        pass

    def store(self, with_transaction=True, use_cache=None):
        """
        Store a new node in the DB, also saving its repository directory
        and attributes.

        After being called attributes cannot be
        changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and
            for which also the parent node is already stored, will be
            automatically stored. The others will remain unstored.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        # TODO: This needs to be generalized, allowing for flexible methods
        # for storing data and its attributes.

        # As a first thing, I check if the data is storable
        if not self._storable:
            raise StoringNotAllowed(self._unstorable_message)

        # Second thing: check if it's valid
        self._validate()

        if self._to_be_stored:

            # Verify that parents are already stored. Raises if this is not the case.
            self._check_are_parents_stored()

            # Get default for use_cache if it's not set explicitly.
            if use_cache is None:
                use_cache = get_use_cache(type(self))
            # Retrieve the cached node.
            same_node = self._get_same_node() if use_cache else None
            if same_node is not None:
                self._store_from_cache(same_node, with_transaction=with_transaction)
                self._add_outputs_from_cache(same_node)
            else:
                # call implementation-dependent store method
                self._db_store(with_transaction)

            # Set up autogrouping used by verdi run
            from aiida.orm.autogroup import current_autogroup, Autogroup, VERDIAUTOGROUP_TYPE
            from aiida.orm import Group

            if current_autogroup is not None:
                if not isinstance(current_autogroup, Autogroup):
                    raise ValidationError("current_autogroup is not an AiiDA Autogroup")

                if current_autogroup.is_to_be_grouped(self):
                    group_label = current_autogroup.get_group_name()
                    if group_label is not None:
                        g = Group.objects.get_or_create(label=group_label, type_string=VERDIAUTOGROUP_TYPE)[0]
                        g.add_nodes(self)

        # This is useful because in this way I can do
        # n = Node().store()
        return self

    def _store_from_cache(self, cache_node, with_transaction):
        from aiida.orm.mixins import Sealable
        assert self.type == cache_node.type

        self.label = cache_node.label
        self.description = cache_node.description

        for key, value in cache_node.iterattrs():
            if key != Sealable.SEALED_KEY:
                self._set_attr(key, value)

        self.folder.replace_with_folder(cache_node.folder.abspath, move=False, overwrite=True)

        # Make sure the node doesn't have any RETURN links
        if cache_node.get_outgoing(link_type=LinkType.RETURN).all():
            raise ValueError('Cannot use cache from nodes with RETURN links.')

        self.store(with_transaction=with_transaction, use_cache=False)
        self.set_extra('_aiida_cached_from', cache_node.uuid)

    def _add_outputs_from_cache(self, cache_node):
        # Add CREATE links
        for entry in cache_node.get_outgoing(link_type=LinkType.CREATE):
            new_node = entry.node.clone()
            new_node.add_incoming(self, link_type=LinkType.CREATE, link_label=entry.link_label)
            new_node.store()

    @abstractmethod
    def _db_store(self, with_transaction=True):
        """
        Store a new node in the DB, also saving its repository directory
        and attributes.

        After being called attributes cannot be
        changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and
            for which also the parent node is already stored, will be
            automatically stored. The others will remain unstored.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        pass


    def get_hash(self, ignore_errors=True, **kwargs):
        """
        Making a hash based on my attributes
        """
        from aiida.common.hashing import make_hash
        try:
            return make_hash(self._get_objects_to_hash(), **kwargs)
        except Exception as e:
            if ignore_errors:
                return None
            else:
                raise e

    def _get_objects_to_hash(self):
        """
        Return a list of objects which should be included in the hash.
        """
        computer = self.get_computer()
        return [
            importlib.import_module(self.__module__.split('.', 1)[0]).__version__, {
                key: val
                for key, val in self.get_attrs().items()
                if (key not in self._hash_ignored_attributes and
                    key not in getattr(self, '_updatable_attributes', tuple()))
            }, self.folder, computer.uuid if computer is not None else None
        ]

    def rehash(self):
        """
        Re-generates the stored hash of the Node.
        """
        self.set_extra(_HASH_EXTRA_KEY, self.get_hash())

    def clear_hash(self):
        """
        Sets the stored hash of the Node to None.
        """
        self.set_extra(_HASH_EXTRA_KEY, None)

    def get_cache_source(self):
        """
        Return the UUID of the node that was used in creating this node from the cache, or None if it was not cached

        :return: the UUID of the node from which this node was cached, or None if it was not created through the cache
        """
        return self.get_extra('_aiida_cached_from', None)

    @property
    def is_created_from_cache(self):
        """
        Return whether this node was created from a cached node.cached

        :return: boolean, True if the node was created by cloning a cached node, False otherwise
        """
        return self.get_cache_source() is not None

    def _get_same_node(self):
        """
        Returns a stored node from which the current Node can be cached, meaning that the returned Node is a valid cache, and its ``_aiida_hash`` attribute matches ``self.get_hash()``.

        If there are multiple valid matches, the first one is returned. If no matches are found, ``None`` is returned.

        Note that after ``self`` is stored, this function can return ``self``.
        """
        try:
            return next(self._iter_all_same_nodes())
        except StopIteration:
            return None

    def get_all_same_nodes(self):
        """
        Return a list of stored nodes which match the type and hash of the current node. For the stored nodes, the ``_aiida_hash`` extra is checked to determine the hash, while ``self.get_hash()`` is executed on the current node.

        Only nodes which are a valid cache are returned. If the current node is already stored, it can be included in the returned list if ``self.get_hash()`` matches its ``_aiida_hash``.
        """
        return list(self._iter_all_same_nodes())

    def _iter_all_same_nodes(self):
        """
        Returns an iterator of all same nodes.
        """
        if not self._cacheable:
            return iter(())

        hash_ = self.get_hash()
        if not hash_:
            return iter(())

        from aiida.orm.querybuilder import QueryBuilder
        builder = QueryBuilder()
        builder.append(self.__class__, filters={'extras._aiida_hash': hash_}, project='*', subclassing=False)
        same_nodes = (n[0] for n in builder.iterall())
        return (n for n in same_nodes if n._is_valid_cache())

    def _is_valid_cache(self):
        """
        Subclass hook to exclude certain Nodes (e.g. failed calculations) from being considered in the caching process.
        """
        return True
