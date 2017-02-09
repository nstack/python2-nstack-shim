import json
import logging
import os
import sys
import traceback
from types import ModuleType

from . import build

logger = logging.getLogger()

SIGNATURE_FILE = os.path.join(os.getcwd(), "nstack-metadata.json")
INTROSPECTION_FILE = os.path.join(os.getcwd(), "dbus-module.xml")
nstack_module = sys.modules[__name__] = ModuleType(__name__)

class DBusWrapper(object):
    """ Proxy object that intercepts all requests, unpacks/packs as needed, and
    forwards on to the user service"""

    @classmethod
    def update_dbus(cls):
        with open(INTROSPECTION_FILE, "r") as f:
          cls.dbus = f.read()

    def __init__(self, service):
        self.update_dbus()
        try:
          self.service = nstack_module._wrapObject(service)
        except AttributeError:
          logger.exception("error wrapping service object")
          self.service = service

    def __getattr__(self, method_name):
        def method(args):
            return self._make_call(method_name, args)
        return method

    def _make_call(self, method_name, args):
        """dynamically call into the user service"""
        logger.debug("data in: {}".format(args))
        func = getattr(self.service, method_name)
        try:
            r = func(args)
        except Exception:
            logger.exception("error calling service method: {} with args: {}".format(
                method_name, args))
            raise
        logger.debug("data out: {}".format(r))
        return r

class BaseService(object):
    def __init__(self):
        self.startup()
        logger.info("Starting service...")

    def Quit(self):
        self.shutdown()
        logger.info("...stopping service")

    def startup(self):
        pass

    def shutdown(self):
        pass

# update the nstack module dict
nstack_module.__dict__.update({
    '__file__': __file__,
    '__doc__': __doc__,
    '__path__': __path__,
    '__package__': __package__,
    #'__all__': ['_types'],
    'DBusWrapper': DBusWrapper,
    'BaseService': BaseService,
})

# add the base types and wrapObject function from the signature to the nstack_module
if(os.path.exists(SIGNATURE_FILE)):
    with open(SIGNATURE_FILE) as f:
        data = json.load(f)
        a, b = build.process_schema(data["api"])
        for i, j in a.items():
            setattr(nstack_module, i, j)
        setattr(nstack_module, '_wrapObject', b)

