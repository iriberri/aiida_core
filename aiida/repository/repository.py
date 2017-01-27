# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

class Repository(object):
    """
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, repo_config):
        """
        Required parameters are going to be implementation specific

        :param repo_config: dictionary with configuration details for repository
        """
        raise NotImplementedError


    def get_name(self):
        """
        Return the name of the repository which is a human-readable label

        :return name: the human readable label associated with this repository
        """
        raise NotImplementedError


    def get_uuid(self):
        """
        Return the UUID identifying the repository.
        Each implementation will decide how to store it: 
        e.g. in a FS it could be a file repo_uuid.txt in the main folder,
        in a object store it could be stored under a key name 'repo_uuid' (making
        sure no object can be stored with the same name) etc.

        :return uuid: the uuid associated with this repository
        :raise ValueError: raises exception if the file that should contain the repo uuid cannot be read
        """
        raise NotImplementedError


    def exists(self, key):
        """
        Determine whether the object identified by key exists and is readable

        :return boolean: returns True if the object exists and is readable, False otherwise
        """
        raise NotImplementedError


    def put_object(self, key, source, stop_if_exists=False):
        """
        Store a new object under 'key' with contents 'source' if it does not yet exist.
        Overwrite an existing object if stop_if_exists is set to False.
        Raise an exception if stop_if_exists is True and the object already exists.

        :param key: fully qualified identifier for the object within the repository
        :param source: filelike object with the content to be stored
        :param stop_if_exists:
        """
        raise NotImplementedError


    def put_new_object(self, key, source):
        """
        Store a new object under 'key' with contents 'source'
        If the provided key already exists, it will be adapted to
        ensure that it is unique. The eventual key under which the
        newly created object is stored is returned upon success

        :param key: fully qualified identifier for the object within the repository
        :param source: filelike object with the content to be stored
        :return: the key of the newly generated object
        """
        raise NotImplementedError


    def get_object(self, key):
        """
        Return the content of a object identified by key

        :param key: fully qualified identifier for the object within the repository
        :raise ValueError: raises exception if given key can not be resolved to readable object
        """
        raise NotImplementedError


    def del_object(self, key):
        """
        Delete the object from the repository

        :param key: fully qualified identifier for the object within the repository
        :raises: raises exception if given key can not be resolved to existing object
        """
        raise NotImplementedError