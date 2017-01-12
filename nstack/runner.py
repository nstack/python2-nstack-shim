#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo NStack service
"""
import os
import signal
import sys
import argparse

from gi.repository import GLib, GObject
from pydbus import SessionBus

import nstack
from service import Service

def sigterm_handler(signo, frame):
    print("Received shutdown signal".format(signo))
    sys.exit(0)

def init_system():
    # Because systemd-nspawn is not connect to a TTY, python will
    # open stdout and stderr in default file buffering mode. However,
    # we want line buffering mode.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)
    # install signal handler
    signal.signal(signal.SIGTERM, sigterm_handler)

def main():
    init_system()

    # get the service name
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help="Service Name")
    args = parser.parse_args()

    # setup the main loop
    loop = GObject.MainLoop()

    # publish on dbus and start main loop
    try:
        with SessionBus().publish(args.name, nstack.DBusWrapper(Service())):
            loop.run()
    except KeyboardInterrupt:
        loop.quit()

    return 0


if __name__ == '__main__':
    sys.exit(main())
