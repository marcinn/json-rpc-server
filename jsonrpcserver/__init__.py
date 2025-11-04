"""A simple JSON-RPC server."""

import collections.abc
import inspect
import json
import logging

log = logging.getLogger(__name__)


class BaseJsonRpcException(Exception):
    """Base JSON-RPC exception"""

    code = -32603

    def __init__(self, message=None, data=None):
        super().__init__(message)
        self.message = message
        self.data = data


class AlreadyRegistered(Exception):
    """Method already registered"""


class InvalidParametersException(BaseJsonRpcException):
    """Invalid method parameters"""

    code = -32602

    def __init__(self, message=None, data=None):
        super().__init__(message=message, data=data)


class RpcException(BaseJsonRpcException):
    """Custom JSON-RPC exception"""

    def __init__(self, code, message=None, data=None):
        if -32768 <= code <= -32000:
            raise ValueError(
                "Codes between (-32768, -32000) are reserved for internal use only"
            )
        self.code = code
        super().__init__(message, data=data)


class Result:
    """JSON-RPC success response"""

    def __init__(self, id_, result):
        self.version = "2.0"
        self.id = id_
        self.result = result

    def as_dict(self):
        """Return the response as a dictionary."""
        return {
            "jsonrpc": self.version,
            "id": self.id,
            "result": self.result,
        }


class Error:
    """JSON-RPC error response"""

    def __init__(self, id_, message, code, data=None):
        self.version = "2.0"
        self.id = id_
        self.message = message
        self.code = int(code)
        self.data = data

    def as_dict(self):
        """Return the response as a dictionary."""

        error = {
            "message": self.message,
            "code": self.code,
        }

        if self.data is not None:
            error["data"] = self.data

        return {
            "jsonrpc": self.version,
            "id": self.id,
            "error": error,
        }


class MethodNotFoundError(Error):
    """Method not found"""

    def __init__(self, id_, method, data=None):
        super().__init__(id_, f"Method not found `{method}`", -32601, data=data)


class InvalidRequestError(Error):
    """Invalid JSON-RPC request"""

    def __init__(self, id_, message, data=None):
        super().__init__(id_, message, -32600, data=data)


class ParseError(Error):
    """Request is not a valid JSON"""

    def __init__(self, message, data=None):
        super().__init__(
            None, f"Server received invalid JSON: {message}", -32700, data=data
        )


class InvalidParametersError(Error):
    """Invalid method parameters"""

    def __init__(self, id_, message=None, data=None):
        super().__init__(
            id_, message or "Invalid parameters number or format", -32602, data=data
        )


class InternalError(Error):
    """Internal server error"""

    def __init__(self, id_, message=None, data=None):
        super().__init__(id_, message or "Internal Error", -32603, data=data)


class Service:
    """JSON-RPC service"""

    def __init__(self):
        self._methods = {}
        self.register("trait_names", self.trait_names)
        self.register("_getAttributeNames", self.get_attribute_names)

        self._validate_method_args = True

    def handle_http_request(self, request):
        """
        Handle HTTP request

        :param request: Python object with `body` attribute which must contain
                        stringified JSON-RPC request object

        Returns:
            stringified JSON-RPC response
        """

        return self.handle_request_body(request.body, request)

    def handle_request_body(self, body, http_request=None):
        log.debug("Got request raw body: %s", body)
        request_dict = self.parse_request_body(body)

        if "error" in request_dict:
            response = request_dict
        else:
            response = self.dispatch(request_dict, http_request)

        try:
            if not response:
                response = ""
            elif isinstance(response, dict):
                response = json.dumps(response)
            else:
                response = json.dumps(response.as_dict())
            log.debug("Sending raw response: %s", response)
            return response
        except (TypeError, ValueError) as ex:
            log.debug("Internal error: %s", ex)

            return json.dumps(InternalError(request_dict.get("id"), str(ex)).as_dict())

    def parse_request_body(self, body):
        """Parse request body and return a Python dictionary"""

        try:
            return json.loads(body)
        except (ValueError, TypeError) as ex:
            log.debug("Parse error: %s", ex)
            return ParseError(str(ex)).as_dict()

    def dispatch(self, request, http_request=None):
        """Find and call a method described in the request"""

        id_ = request.get("id", None)

        log.debug("Dispatching request ID: %s", id_)
        try:
            version = request["jsonrpc"]
        except KeyError:
            log.debug("Missing `jsonrpc` key in request payload")
            return InvalidRequestError(id_, "Missing `jsonrpc` key in request object")

        if not version == "2.0":
            log.debug("Requested unsupported JSON-RPC version: %s", version)
            return InvalidRequestError(
                id_,
                "Server supports only version 2.0 of the JSON-RPC protocol",
            )

        try:
            method = request["method"]
        except KeyError:
            log.debug("Missing `method` key in request payload")
            return InvalidRequestError(id_, "Missing `method` key in request object")

        try:
            log.debug("Calling method `%s`", method)
            method = self._methods[method]
        except KeyError:
            log.debug("Method not found: `%s`", method)
            return MethodNotFoundError(id_, method)

        args = []
        kwargs = {}

        try:
            params = request["params"]
        except KeyError:
            pass
        else:
            if params:
                if isinstance(params, collections.abc.Mapping):
                    log.debug("Assuming params as a dictionary-like object")
                    kwargs = params
                else:
                    log.debug("Assuming params as a list-like object")
                    args = params

        if method["takes_http_request"]:
            args = [http_request] + args

        if self._validate_method_args:
            try:
                inspect.signature(method["callback"]).bind(*args, **kwargs)
            except TypeError as ex:
                log.debug("Invalid method parameters: %s", ex)
                return InvalidParametersError(id_, data=str(ex))

        try:
            result = method["callback"](*args, **kwargs)
        except BaseJsonRpcException as ex:
            return Error(id_, ex.message, ex.code, data=ex.data)

        return Result(id_, result)

    def method(self, method=None, takes_http_request=False):
        """
        Register a method

        It can be used as a decorator.

        :param method:             Method name
        :param takes_http_request: Method will be given a HTTP request object
                                   as a first argument
        """

        if callable(method):
            self.register(method.__name__, method, takes_http_request)
            return method

        def wrapper(func):
            self.register(method or func.__name__, func, takes_http_request)
            return func

        return wrapper

    def register(self, method, func, takes_http_request=False):
        """
        Register a method

        :param method:             Method name
        :param func:               A function to be called
        :param takes_http_request: Method will be given a HTTP request object
                                   as a first argument
        """

        if method in self._methods:
            raise AlreadyRegistered(f"Method `{method}` already registered.")

        log.debug("Registering method `%s`", method)
        self._methods[method] = {
            "callback": func,
            "takes_http_request": takes_http_request,
            "argspec": inspect.getfullargspec(func),
        }

    def trait_names(self):
        """Return a list of public method names"""

        return self.public_methods().keys()

    def get_attribute_names(self):
        """Used by XML-RPC, not implemented"""

        return []

    def public_methods(self):
        """Return a dictionary of public methods"""

        return dict(
            filter(
                lambda x: (not x[0].startswith("_") and not x[0] == "trait_names"),
                self._methods.items(),
            )
        )
