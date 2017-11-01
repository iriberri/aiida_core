# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import os
import errno

from aiida.backends import settings
from aiida.common.exceptions import ConfigurationError, MissingConfigurationError
from aiida.common.setup import (get_config, get_secret_key, get_property,
                                get_profile_config, get_default_profile,
                                parse_repository_uri)



USE_TZ = True

try:
    confs = get_config()
except MissingConfigurationError:
    raise MissingConfigurationError("Please run the AiiDA Installation, no config found")

if settings.AIIDADB_PROFILE is None:
    raise ConfigurationError("AIIDADB_PROFILE not defined, did you load django "
                             "through the AiiDA load_dbenv()?")

profile_conf = get_profile_config(settings.AIIDADB_PROFILE, conf_dict=confs)

# put all database specific portions of settings here
BACKEND = profile_conf.get('AIIDADB_BACKEND', 'django')
DBENGINE = profile_conf.get('AIIDADB_ENGINE', '')
DBNAME = profile_conf.get('AIIDADB_NAME', '')
DBUSER = profile_conf.get('AIIDADB_USER', '')
DBPASS = profile_conf.get('AIIDADB_PASS', '')
DBHOST = profile_conf.get('AIIDADB_HOST', '')
DBPORT = profile_conf.get('AIIDADB_PORT', '')
REPOSITORY_BASE_PATH = profile_conf.get('REPOSITORY_BASE_PATH', '')

# if not os.path.isdir(REPOSITORY_BASE_PATH):
#     try:
#         os.makedirs(REPOSITORY_BASE_PATH)
#     except OSError as error:
#         if error.errno == errno.EEXIST and os.path.isdir(REPOSITORY_BASE_PATH):
#             pass
#         else:
#             raise







def get_repository_config(name = ''):
    """
    Documentation string
    """
    try:
        repository_conf      = profile_conf['repository']
        repository_available = repository_conf['available']
        repository_default   = repository_conf['default']
    except Exception as exception:
        raise ConfigurationError("Invalid repository configuration")

    if not name:
        repository_name = repository_default
    else:
        repository_name = name

    try:
        repository_config = repository_available[repository_name]
    except Exception as exception:
        raise ConfigurationError("The chosen repository '{}' is not defined in the configuration".format(repository_name))

    return repository_name, repository_config


def get_repository(name = ''):
    """
    Documentation string
    """
    import tempfile
    import urlparse
    import errno
    import StringIO
    import uuid as UUID

    from aiida.repository.implementation.filesystem.repository import RepositoryFileSystem
    from aiida.repository.implementation.swift.repository import RepositorySwift

    try:
        repository_name, repository_config = get_repository_config(name)
    except Exception as exception:
        raise

    try:
        repository_type = repository_config['type'];
    except Exception as exception:
        raise ConfigurationError("The chosen repository '{}' does not specify a type in 'type'".format(repository_name))


    if repository_type == 'filesystem':
        base_url  = repository_config.get('base_url', '')
        uuid_file = repository_config.get('uuid_file', '')

        parsed_base_url   = urlparse.urlparse(base_url)
        repository_scheme = parsed_base_url.scheme
        repository_path   = os.path.normpath(parsed_base_url.path)

        # At this point configured repositories should have been created and initialized
        # so we verify that the prerequisite resources exist and are accessible
        if repository_scheme != 'file':
            raise ConfigurationError("The protocol for a filesystem repository should be 'file://'")

        # Check if the repository directory is writable
        try:
            tempfile = tempfile.TemporaryFile(dir=repository_path)
            tempfile.close()
        except OSError as e:
            raise ConfigurationError("The configured base path '{}' is not writable".format(repository_path))

        # Check if the UUID file is readable
        try:
            uuid_path = os.path.join(repository_path, uuid_file)
            with open(uuid_path, 'rb') as fp:
                fp.read()
        except IOError as e:
            raise ConfigurationError("The configured uuid file '{}' is not readable".format(uuid_path))

        repo_config = {
            'repo_name'    : repository_name,
            'base_path'    : repository_path,
            'uuid_path'    : uuid_path,
        }

        repository = RepositoryFileSystem(repo_config)

    elif repository_type == 'swift':
        from swiftclient.client import ClientException
        uuid_key     = repository_config.get('uuid_key', '')
        auth_url     = repository_config.get('auth_url', '')
        auth_version = repository_config.get('auth_version', '')
        auth_user    = repository_config.get('auth_user', '')
        auth_key     = repository_config.get('auth_key', '')
        container    = repository_config.get('container', '')

        repo_config = {
            'repo_name'    : repository_name,
            'uuid_key'     : uuid_key,
            'auth_url'     : auth_url,
            'auth_version' : auth_version,
            'auth_user'    : auth_user,
            'auth_key'     : auth_key,
            'container'    : container,
        }

        repository = RepositorySwift(repo_config)
        repository.put_object(uuid_key, StringIO.StringIO(UUID.uuid4()))

    else:
        raise ConfigurationError("Unknown repository type '{}'".format(repository_type))

    return repository