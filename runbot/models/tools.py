import socket
import time
import os
import signal
import re
import logging
import fcntl

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


def fqdn():
    return socket.getfqdn()


def log(*l, **kw):
    out = [i if isinstance(i, str) else repr(i) for i in l] + ["%s=%r" % (k, v) for k, v in kw.items()]
    _logger.debug(' '.join(out))


def dashes(string):
    """Sanitize the input string"""
    for i in '~":\'':
        string = string.replace(i, "")
    for i in '/_. ':
        string = string.replace(i, "-")
    return string


def mkdirs(dirs):
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)


def grep(filename, string):
    if os.path.isfile(filename):
        return open(filename).read().find(string) != -1
    return False


def rfind(filename, pattern):
    """Determine in something in filename matches the pattern"""
    if os.path.isfile(filename):
        regexp = re.compile(pattern, re.M)
        with open(filename, 'r') as f:
            if regexp.findall(f.read()):
                return True
    return False


def lock(filename):
    fd = os.open(filename, os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def locked(filename):
    result = False
    try:
        fd = os.open(filename, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            result = True
        os.close(fd)
    except OSError:
        result = False
    return result


def nowait():
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)


def run(l, env=None):
    """Run a command described by l in environment env"""
    log("run", l)
    env = dict(os.environ, **env) if env else None
    if isinstance(l, list):
        if env:
            rc = os.spawnvpe(os.P_WAIT, l[0], l, env)
        else:
            rc = os.spawnvp(os.P_WAIT, l[0], l)
    elif isinstance(l, str):
        tmp = ['sh', '-c', l]
        if env:
            rc = os.spawnvpe(os.P_WAIT, tmp[0], tmp, env)
        else:
            rc = os.spawnvp(os.P_WAIT, tmp[0], tmp)
    log("run", rc=rc)
    return rc


def now():
    return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)


def dt2time(datetime):
    """Convert datetime to time"""
    return time.mktime(time.strptime(datetime, DEFAULT_SERVER_DATETIME_FORMAT))


def s2human(time):
    """Convert a time in second into an human readable string"""
    for delay, desc in [(86400, 'd'), (3600, 'h'), (60, 'm')]:
        if time >= delay:
            return str(int(time / delay)) + desc
    return str(int(time)) + "s"
