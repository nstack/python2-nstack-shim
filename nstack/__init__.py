import json
import os
import sys
from types import ModuleType

from . import build

SIGNATURE_FILE = os.path.join(os.getcwd(), "nstack-metadata.json")
INTROSPECTION_FILE = os.path.join(os.getcwd(), "dbus-module.xml")

class DBusWrapper(object):
    """ Proxy object that intercepts all requests, unpacks/packs as needed, and
    forwards on to the user service"""

    @classmethod
    def update_dbus(cls):
        with open(INTROSPECTION_FILE, "r") as f:
          cls.dbus = f.read()

    def __init__(self, service):
        self.update_dbus()
        self.service = service

    def __getattr__(self, method_name):
        def method(args):
            return self._make_call(method_name, args)
        return method

    def _make_call(self, method_name, args):
        """dynamically call into the user service"""
        func = getattr(self.service, method_name)
        return func(args)


class BaseService(object):
    def __init__(self):
        self.startup()
        print("Starting service...")

    def Quit(self):
        self.shutdown()
        print("...stopping service")

    def startup(self):
        pass

    def shutdown(self):
        pass

new_module = sys.modules[__name__] = ModuleType(__name__)
new_module.__dict__.update({
    '__file__': __file__,
    '__doc__': __doc__,
    '__path__': __path__,
    '__package__': __package__,
    #'__all__': ['_types'],
    'DBusWrapper': DBusWrapper,
    'BaseService': BaseService,
})

if os.path.exists(SIGNATURE_FILE):
    with open(SIGNATURE_FILE) as f:
        data = json.load(f)["api"]
        a, b = build.process_schema(data)
        for i, j in a.items():
            setattr(new_module, i, j)
            setattr(new_module, '_wrapObject', b)
