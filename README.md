# JSON-RPC Server for Python

This is damn simple, framework-agnostic JSON-RPC v2.0 server for Python.

**This package has no dependencies.**
You can build service API without thinking about any framework nor toolkit, and even without thinking about HTTP itself.
This package is an implementation of JSON-RPC protocol only, following rules described on http://www.jsonrpc.org/specification

## What is JSON-RPC?

JSON-RPC is a protocor similar to XML-RPC, but simpler and very lightweight.
There is no necessary to generate nor parse XML documents by using heavy librariers. 

You can build easily remote services and call them using clients implemented in many languages.
JSON-RPC services are always exposed using HTTP(S) protocol.

For more information please read JSON-RPC v2.0 specification: http://www.jsonrpc.org/specification

## Getting started

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

If you need quickly expose your service using Django, just use `jsonrpcserver-django` package,
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

JSON-RPC `Service` class has very simple API based on str/unicode. 
The `Service.call` method expects that input string will be a representation of a JSON-RPC Request object.

In the similar way `Service.call` will return a str/unicode with a JSON-RPC Response object representation 
(success and error responses are returned same way, as described in http://www.jsonrpc.org/specification, but contain `result` and `error` keys respectively).

Pseudocode:
```
def my_adaptor(request):
   body = getRawRequestBody()
   return callJSONRPCService(body)
```

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
