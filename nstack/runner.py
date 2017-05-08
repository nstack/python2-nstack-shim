#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo NStack service
"""
import logging
import os
import signal
import sys
import argparse

logger = logging.getLogger('python-runner')

# Because systemd-nspawn is not connect to a TTY, python will
# open stdout and stderr in default file buffering mode. However,
# we want line buffering mode.
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

try:
    from gi.repository import GLib
except ImportError:
    # support pgi as a fallback
    # for use in non-system pythons
    import pgi
    pgi.install_as_gi()
    from pgi.repository import GLib

from pydbus import SessionBus

import nstack
from service import Service

def sigterm_handler(signo, frame):
    logger.warn("Received shutdown signal".format(signo))
    sys.exit(0)

# determine if the function under this name is a sink
def is_sink(name):
    return nstack.data['api']['signatures'][name][1]['type'][0] == "void"

def main():
    # install signal handler
    signal.signal(signal.SIGTERM, sigterm_handler)

    # get the service name
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action="store_true", help="Enable debugging")
    # service_name looks something like nstackmodule.foo.id40
    parser.add_argument('service_name', help="Service Name")
    # function_name is the name of the python function that will be called
    # through dbus from this container
    parser.add_argument('function_name', help="Service Name")
    args = parser.parse_args()
    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=loglevel)
    if args.debug:
        logger.debug("Enabled debug logging!")

    # setup the main loop
    loop = GLib.MainLoop()
    bus = SessionBus()
    # publish on dbus and start main loop

    if is_sink(args.function_name):
        out = None
    else:
        out = bus.get("{}.callback".format(args.service_name),
                    "/com/nstack/service/callback")
    try:
        with bus.publish(args.service_name, nstack.DBusWrapper(out, Service())):
            loop.run()
    except KeyboardInterrupt:
        loop.quit()

    return 0

if __name__ == '__main__':
    sys.exit(main())
