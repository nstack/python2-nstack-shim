import json
import logging
import os
import reprlib
import sys
import traceback
from types import GeneratorType, ModuleType

from . import build

logger = logging.getLogger('python-service')

SIGNATURE_FILE = os.path.join(os.getcwd(), "nstack-metadata.json")
INTROSPECTION_FILE = os.path.join(os.getcwd(), "dbus-module.xml")
nstack_module = sys.modules[__name__] = ModuleType(__name__)

# load the api definition from the json file
# the file is absent when running unit tests, hence the if statement
# (see https://stackhut.slack.com/archives/C21MX7TUG/p1494339914372158)
if(os.path.exists(SIGNATURE_FILE)):
    with open(SIGNATURE_FILE) as f:
        data = json.load(f)
else:
    data = None

class DBusWrapper(object):
    """ Proxy object that intercepts all requests, unpacks/packs as needed, and
    forwards on to the user service"""

    @classmethod
    def update_dbus(cls):
        with open(INTROSPECTION_FILE, "r") as f:
          cls.dbus = f.read()

    def __init__(self, out, service):
        # Note: out is None if this is a sink
        self.out = out
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
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("{}, data in: {}".format(method_name, reprlib.repr(args)))
        func = getattr(self.service, method_name)
        try:
            r = func(args)
        except Exception:
            logger.exception("error calling service method: {} with args: {}".format(
                method_name, args))
            raise
        if not isinstance(r, GeneratorType):
            r = [r]
        out = self.out
        if out is None:
            logger.debug("{} is sink, no data is sent back.".format(method_name))
        else:
            try:
                for item in r:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("{}, data out: {}".format(method_name, reprlib.repr(item)))
                    out.callback(item)
            except Exception:
                logger.exception("error iterating results for method: {} with args: {}".format(
                    method_name, args))
                raise
            logger.debug("{}, data finished.".format(method_name))
        return None

class BaseService(object):
    def __init__(self):
        self.args = json.loads(os.environ['NSTACK_ARGS']) if 'NSTACK_ARGS' in os.environ else {}
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
    'data': data
})

# add the base types and wrapObject function from the signature to the nstack_module
if data is not None:
    a, b, c = build.process_schema(data["api"], nstack_module)
    setattr(nstack_module, '_wrapObject', b)

