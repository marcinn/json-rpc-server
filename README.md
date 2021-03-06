
![PyPI](https://img.shields.io/pypi/v/damn-simple-jsonrpc-server.svg)
![Downloads](https://pepy.tech/badge/damn-simple-jsonrpc-server)
![Coverage Status](https://coveralls.io/repos/github/marcinn/json-rpc-server/badge.svg?branch=master)


# JSON-RPC Server for Python

This is a core implementation of JSON-RPC v2.0 server for Python.

Available adapters:
- [Django](https://github.com/marcinn/json-rpc-server-django/)

## Features

- Service oriented 
- No external dependencies
- Easy integration with frameworks

## Roadmap

- 0.6: type hinting
- 0.7: async support
- 1.0: final/stable version

## Getting started

### Installation

```
pip install damn-simple-jsonrpc-server
```

### Calculator service example

Let's make calculator service which supports `add` and `subtract` operations. 

(calculator_service.py)
```python

import jsonrpcserver as rpc

calculator = rpc.Service()

@calculator.method
def add(x, y):
    return x+y

@calculator.method('subtract')
def sub(x, y):
    return x-y
    
```

Well... it's done. But where it is accessible? Nowhere! 
You can access it directly by `calculator` variable, but this is nonsense.
This is an API for HTTP adapters, but not for humans.


### Exposing JSON-RPC service via HTTP

Simplest way to expose `calculator` service is to use well-known HTTP framework.
It may be a Django, for example:

(urls.py)
```python

from django.conf.urls import patterns, include, url
from .calculator_service import calculator

def calculator_service_view(request):
    return calculator.handle_request_body(request.body)

urlpatterns = patterns('',
        url(r'^$', calculator_service_view, name='calculator'),
)
```

But there is a simpler way! :)


#### Using existing adaptors

If you need quickly expose your service using Django, just use [damn simple JSON-RPC Django adaptor](https://pypi.python.org/pypi/damn-simple-jsonrpc-server-django),
which contains ready to use adaptor:

(urls.py)
```python
from django.conf.urls import patterns, include, url
from calculator_service import calculator

urlpatterns = patterns('',
        url(r'^$', 'jsonrpcdjango.serve', kwargs={'service': calculator},
            name='calculator'),
)
```

That's all. Nothing more, nothing less!


### Writing custom adaptors

JSON-RPC `Service` class has very simple API based on str/unicode or request-like object.
You may use one of the following methods available in `Service` class:
  - `handle_request_body`
  - `handle_http_request`
  
The `handle_request_body` method expects that input string will be a representation of a JSON-RPC Request object. 

The `handle_http_request` method expects that request-like object will be passed as an argument. 
In that case request-like object **must** contain `body` attribute with string representation 
of JSON-RPC request.

Return value of `handle_request_body` and `handle_http_request` is always a str/unicode
with a JSON-RPC Response object representation (success and error responses are returned
same way, as described in http://www.jsonrpc.org/specification, but will contain `result`
and `error` keys respectively).


## Authentication, CSRF, other stuff...

Authentication and CSRF are HTTP-related topics. 
You may implement them in adaptors or just use tools from your favourite HTTP framework.
For Django framework you may simply decorate whole service:

(urls.py)
```python
import jsonrpcdjango as rpc

[...]

urlpatterns = patterns('',
        url(r'^$', login_required(rpc.serve), kwargs={'service': calculator},
            name='calculator'),
```

To enable or disable CSRF just use specific adaptor:
  - `jsonrpcdjango.serve` for CSRF-less handler
  - `jsonrpcdjango.csrf_serve` for CSRF-protected handler
  - or use disrectly Django's decorators `csrf_exempt`, `csrf_protect` or enable `CsrfViewMiddleware` (read https://docs.djangoproject.com/en/dev/ref/csrf/ for details) 

*Currently there is no possibility to decorate specific methods of the service with `jsonrpcdjango` adaptor.*

## Authorization

If you want add authorization to your method you should use similar solution as for authentication. 
For Django framework you may simply decorate whole service:

(urls.py)
```python
import jsonrpcdjango as rpc

[...]

urlpatterns = patterns('',
        url(r'^$', permission_required('can_use_rpc')(rpc.serve), kwargs={'service': calculator},
            name='calculator'),
```

*Currently there is no possibility to decorate specific methods of the service with `jsonrpcdjango` adaptor.*

## Accessing original HTTP request inside service methods

Sometimes you may need access to specific request data added somewhere
in middleware stack. In that case you can register JSON-RPC method with
additional argument `takes_http_request=True`. Original `request` object
will be passed as first argument.

If you're using Django as an HTTP framework and `jsonrpcdjango` adaptor,
you can provide access to Django's `HttpRequest` object inside service method
without any hacks. Just declare `takes_http_request=True` at registering
time. This will make your service dependend on Django, but will add more flexibility.


(calculator_service.py)
```python

calculator = rpc.Service()

[...]

@calculator.method(takes_http_request=True)
def beast_add(request, x, y):
    if request.user.is_superuser:
        return x+y
    else:
        return 666

```

## What is JSON-RPC?

JSON-RPC is a protocor similar to XML-RPC, but simpler and very lightweight.
There is no necessary to generate nor parse XML documents by using heavy librariers. 

For more information please read JSON-RPC v2.0 specification: http://www.jsonrpc.org/specification

