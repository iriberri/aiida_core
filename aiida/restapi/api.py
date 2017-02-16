"""
Implementation of RESTful API for materialscloud.org based on flask + flask_restful module
For the time being the API returns the parsed valid endpoints upon GET request
Author: Snehal P. Waychal and Fernando Gargiulo @ Theos, EPFL
"""

from flask_restful import Api
from aiida.restapi.resources import Calculation, Computer, Code, Data, Group, \
    Node, User


from flask import Flask, jsonify
from aiida.restapi.common.exceptions import RestInputValidationError,\
    RestValidationError

## Instaniate a Flask an app
app = Flask(__name__)

# Error handling for error raised by invalid urls (not by non-existing
# resources!)
# @app.errorhandler(Exception)
# def error_handler(error):
#     if isinstance(error, RestValidationError):
#         response = jsonify({'message': error.message})
#         response.status_code = 400
#     elif isinstance(error, RestInputValidationError):
#         response = jsonify({'message': error.message})
#         response.status_code = 400
#     # Generic server-side error (not to make the api crash if an unhandled
#     # exception is raised. Caution is never enough!!)
#     else:
#         response = jsonify({'message': 'Internal server error. The original '
#                                        'message was: \"{}\"'.format(
#             error.message)})
#         response.status_code = 500
#
#     return response

# Defined a derived flask_restful Api with some customization
class AiidaApi(Api):
    """
    AiiDA RESTful API class ...
    """

    def __init__(self, app, **kwargs):
        """
        The need to have a special constructor is to include directly the
        addition of resources with the parameters required to initialize the
        resource classes.

        Args:
            **kwargs: parameters to be passed to the resources for
            configuration and PREFIX
        """

        super(AiidaApi, self).__init__(app=app, prefix=kwargs['PREFIX'])

        ## Add resources to the api
        self.add_resource(Computer,
                         # supported urls
                         '/computers/',
                         '/computers/schema/',
                         '/computers/statistics/',
                         '/computers/page/',
                         '/computers/page/<int:page>/',
                         '/computers/<int:pk>/',
                         '/computers/schema/',
                         strict_slashes=False,
                         resource_class_kwargs=kwargs)

        self.add_resource(Node,
                         '/nodes/',
                         '/nodes/schema/',
                         '/nodes/statistics/',
                         '/nodes/page/',
                         '/nodes/page/<int:page>/',
                         '/nodes/<int:pk>/',
                         '/nodes/<int:pk>/io/inputs/',
                         '/nodes/<int:pk>/io/inputs/page/',
                         '/nodes/<int:pk>/io/inputs/page/<int:page>/',
                         '/nodes/<int:pk>/io/outputs/',
                         '/nodes/<int:pk>/io/outputs/page/',
                         '/nodes/<int:pk>/io/outputs/page/<int:page>/',
                         '/nodes/<int:pk>/io/tree/',
                         '/nodes/<int:pk>/content/attributes/',
                         '/nodes/<int:pk>/content/extras/',
                         '/nodes/statistics/',
                         strict_slashes=False,
                         resource_class_kwargs=kwargs)

        self.add_resource(Calculation,
                         '/calculations/',
                         '/calculations/schema/',
                         '/calculations/statistics/',
                         '/calculations/page/',
                         '/calculations/page/<int:page>/',
                         '/calculations/<int:pk>/',
                         '/calculations/<int:pk>/io/inputs/',
                         '/calculations/<int:pk>/io/inputs/page/',
                         '/calculations/<int:pk>/io/inputs/page/<int:page>/',
                         '/calculations/<int:pk>/io/outputs/',
                         '/calculations/<int:pk>/io/outputs/page/',
                         '/calculations/<int:pk>/io/outputs/page/<int:page>/',
                         '/calculations/<int:pk>/io/tree/',
                         '/calculations/<int:pk>/content/attributes/',
                         '/calculations/<int:pk>/content/extras/',
                         '/calculations/schema/',
                         '/calculations/statistics/',
                         strict_slashes=False,
                         resource_class_kwargs=kwargs)

        self.add_resource(Data,
                         '/data/',
                         '/data/schema/',
                         '/data/statistics/',
                         '/data/page/',
                         '/data/page/<int:page>',
                         '/data/<int:pk>/',
                         '/data/<int:pk>/io/inputs/',
                         '/data/<int:pk>/io/inputs/page/',
                         '/data/<int:pk>/io/inputs/page/<int:page>/',
                         '/data/<int:pk>/io/outputs/',
                         '/data/<int:pk>/io/outputs/page/',
                         '/data/<int:pk>/io/outputs/page/<int:page>/',
                         '/data/<int:pk>/io/tree/',
                         '/data/<int:pk>/content/attributes/',
                         '/data/<int:pk>/content/extras/',
                         '/data/schema/',
                         '/data/statistics/',
                         strict_slashes=False,
                         resource_class_kwargs=kwargs)

        self.add_resource(Code,
                         '/codes/',
                         '/codes/schema/',
                         '/codes/statistics/',
                         '/codes/page/',
                         '/codes/page/<int:page>/',
                         '/codes/<int:pk>/',
                         '/codes/<int:pk>/io/inputs/',
                         '/codes/<int:pk>/io/inputs/page/',
                         '/codes/<int:pk>/io/inputs/page/<int:page>/',
                         '/codes/<int:pk>/io/outputs/',
                         '/codes/<int:pk>/io/outputs/page/',
                         '/codes/<int:pk>/io/outputs/page/<int:page>/',
                         '/codes/<int:pk>/io/tree/',
                         '/codes/<int:pk>/content/attributes/',
                         '/codes/<int:pk>/content/extras/',
                         '/codes/schema/',
                         '/codes/statistics/',
                         strict_slashes=False,
                         resource_class_kwargs=kwargs)

        self.add_resource(User,
                         '/users/',
                         '/users/schema/',
                         '/users/statistics/',
                         '/users/page/',
                         '/users/page/<int:page>/',
                         '/users/<int:pk>/',
                         strict_slashes=False,
                         resource_class_kwargs=kwargs)

        self.add_resource(Group,
                         '/groups/',
                         '/groups/schema/',
                         '/groups/statistics/',
                         '/groups/page/',
                         '/groups/page/<int:page>/',
                         '/groups/<int:pk>/',
                         strict_slashes=False,
                         resource_class_kwargs=kwargs)