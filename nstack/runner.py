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
    print("Received shutdown signal".format(signo))
    sys.exit(0)

def main():
    # install signal handler
    signal.signal(signal.SIGTERM, sigterm_handler)

    # get the service name
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help="Service Name")
    parser.add_argument('debug', action="store_true", help="Enable debugging")
    args = parser.parse_args()
    loglevel = logging.DEBUG if args.debug else logging.WARN
    logging.basicConfig(level=loglevel)
    if args.debug:
        logging.getLogger().debug("Enabled debug logging!")

    # setup the main loop
    loop = GLib.MainLoop()

    # publish on dbus and start main loop
    try:
        with SessionBus().publish(args.name, nstack.DBusWrapper(Service())):
            loop.run()
    except KeyboardInterrupt:
        loop.quit()

    return 0

if __name__ == '__main__':
    sys.exit(main())
