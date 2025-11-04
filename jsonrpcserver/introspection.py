import inspect
from textwrap import dedent


def trim_docstring(docstring):
    """
    Cut indentation from docstring

    See http://www.python.org/dev/peps/pep-0257/
    """

    if not docstring:
        return ''
    return dedent(docstring)


def introspect(service, url):
    """Create a structure describing the service"""

    methods = []
    for method, meta in service.public_methods().items():
        callback = meta['callback']
        methods.append({
            'name': method,
            'description': trim_docstring(callback.__doc__),
            'args': meta['argspec'].args,
            'invocation': '%s%s' % (method,
                str(inspect.signature(callback))),
            })
    return {
        'methods': methods,
        'url': url,
        'name': getattr(service, '__name__', service.__class__.__name__),
        'description': trim_docstring(service.__doc__),
    }
