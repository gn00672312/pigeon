#!/usr/bin/python
import time
import sys
import socket

from argparse import ArgumentParser

parser = ArgumentParser('sock', add_help=False)

parser.add_argument('-h', '--hostname', help='-h hostname to test', required=True)
parser.add_argument('-p', '--port', help='-p host port', required=True)
parser.add_argument('-t', '--timeout', help='-t timeout', default=3)
parser.add_argument('--help', action='help', help='show this help message and exit')

name_args, argvs = parser.parse_known_args()
HOSTNAME = name_args.hostname
PORT = int(name_args.port)
TIMEOUT = name_args.timeout


def main(hostname=HOSTNAME, port=PORT, timeout=TIMEOUT):
    print('Wait 5 seconds....')
    time.sleep(5)
    try:
        sock = socket.create_connection((hostname, port), timeout=3)
    except socket.timeout:
        print('Connect to host %s:%d timeout.' % (hostname, port))
        sys.exit(1)
    except socket.error:
        print('Connect to host %s:%d failed.' % (hostname, port))
        sys.exit(1)
    print('Host %s:%d ia alive.' % (hostname, port))


if __name__ == '__main__':
    main()
