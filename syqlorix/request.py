import threading
from functools import wraps

# Create a thread-local storage
_request_ctx = threading.local()

class RequestProxy:
    def __getattr__(self, name):
        return getattr(_request_ctx.request, name)

    def __setattr__(self, name, value):
        if name == '_request_ctx':
            super().__setattr__(name, value)
        else:
            object.__setattr__(_request_ctx.request, name, value)


class Request:
    def __init__(self, path: str, **kwargs):
        self.path = path
        for k,v in kwargs.items():
            object.__setattr__(self, k, v)

request = RequestProxy()

def set_request(**kwargs):
    clear_request()
    _request_ctx.request = Request(**kwargs)

def clear_request():
    if hasattr(_request_ctx, 'request'):
        del _request_ctx.request

