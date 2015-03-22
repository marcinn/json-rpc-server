import collections
import json

import logging
log = logging.getLogger(__name__)



class Result(object):
    def __init__(self, id, result):
        self.version = '2.0'
        self.id = id
        self.result = result

    def as_dict(self):
        return {
                'jsonrpc': self.version,
                'id': self.id,
                'result': self.result,
                }


class Error(object):
    def __init__(self, id, message, code, data=None):
        self.version = '2.0'
        self.id = id
        self.message = message
        self.code = int(code)
        self.data = data

    def as_dict(self):
        error = {
            'message': self.message,
            'code': self.code,
            }

        if self.data is not None:
            error['data'] = self.data

        return {
            'jsonrpc': self.version,
            'id': self.id,
            'error': error,
            }


class MethodNotFoundError(Error):
    def __init__(self, id, method, data=None):
        super(MethodNotFoundError, self).__init__(id,
            'Method not found `%s`' % method, -32601, data=data)


class InvalidRequestError(Error):
    def __init__(self, id, message, data=None):
        super(InvalidRequestError, self).__init__(id, message, -32600,
                data=data)


class ParseError(Error):
    def __init__(self, message, data=None):
        super(ParseError, self).__init__(None,
            'Server received invalid JSON: %s' % message, -32700, data=data)


class InvalidParametersError(Error):
    def __init__(self, id, message=None, data=None):
        super(InvalidParametersError, self).__init__(id,
            message or 'Invalid parameters number or format', -32602, data=data)


class InternalError(Error):
    def __init__(self, id, message=None, data=None):
        super(InternalError, self).__init__(id, message or 'Internal Error',
                -32603, data=data)


class Service(object):
    def __init__(self):
        self._methods = {}

    def handle_request_body(self, request):
        log.debug('Got request raw body: %s', request)
        try:
            request_dict = json.loads(request)
        except (ValueError, TypeError), ex:
            log.debug('Parse error: %s', ex)
            return ParseError(unicode(ex)).as_dict()

        response = self.dispatch(request_dict)

        try:
            response = json.dumps(response.as_dict()) if response else ''
            log.debug('Sending raw response: %s', response)
            return response
        except (TypeError, ValueError), ex:
            log.debug('Internal error: %s', ex)
            return json.dumps(InternalError(request_dict.get('id'),
                    unicode(ex)).as_dict())

    def dispatch(self, request):
        ident = request.get('id')

        log.debug('Dispatching request ID: %s', ident)
        try:
            version = request['jsonrpc']
        except KeyError:
            log.debug('Missing `jsonrpc` key in request payload')
            if ident:
                return InvalidRequestError(ident,
                        'Missing `jsonrpc` key in request object')
            else:
                return

        if not version == '2.0':
            log.debug('Requested unsupported JSON-RPC version: %s', version)
            if ident:
                return InvalidRequestError(ident,
                    'Server supports only version 2.0 of the JSON-RPC protocol')
            else:
                return

        try:
            method = request['method']
        except KeyError:
            log.debug('Missing `method` key in request payload')
            if ident:
                return InvalidRequestError(ident,
                    'Missing `method` key in request object')
            else:
                return

        try:
            log.debug('Calling method `%s`', method)
            method = self._methods[method]
        except KeyError:
            log.debug('Method not found: `%s`', method)
            if ident:
                return MethodNotFoundError(ident, method)
            else:
                return

        args = []
        kwargs = {}

        try:
            params = request['params']
        except KeyError:
            pass
        else:
            if params:
                if isinstance(params, collections.Mapping):
                    log.debug('Assuming params as a dictionary-like object')
                    kwargs = params
                else:
                    log.debug('Assuming params as a list-like object')
                    args = params

        try:
            result = method(*args, **kwargs)
        except TypeError, ex:
            log.debug('Invalid method parameters: %s', ex)
            if ident:
                return InvalidParametersError(ident)

        return Result(ident, result) if ident else None

    def method(self, method):
        if callable(method):
            self.register(method.__name__, method)
            return method
        else:
            def wrapper(func):
                self.register(method, func)
                return func
            return wrapper

    def register(self, method, func):
        if method in self._methods:
            raise AlreadyRegistered('Method `%s` already registered.' % method)

        log.debug('Registering method `%s`', method)
        self._methods[method] = func


