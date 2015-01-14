"""
Configure logging
"""
import logging
import os
import platform
from logging.handlers import SysLogHandler


def configure_logging(app):
    """
    Set the log level for the application
    """

    # Disable log exceptions due to overly long elasticsearch
    # log messages
    logging.raiseExceptions = False
    # Set up format for default logging
    hostname = platform.node().split('.')[0]
    formatter = ('%(asctime)s %(levelname)s %(process)d [%(name)s] '
                 '%(filename)s:%(lineno)d - '
                 '{hostname}- %(message)s').format(hostname=hostname)

    # Grab config from env if set, else allow system/language
    # defaults.
    config_log_level = app.config.get('LOG_LEVEL', None)
    config_log_int = None
    set_level = None

    if config_log_level:
        config_log_int = getattr(logging, config_log_level.upper(), None)
        if not isinstance(config_log_int, int):
            raise ValueError('Invalid log level: {0}'.format(config_log_level))
        set_level = config_log_int

    # Set to NotSet if we still aren't set yet
    if not set_level:
        set_level = config_log_int = logging.NOTSET

    # Setup logging with format and main and change the root logger if
    # we aren't.
    logging.basicConfig(format=formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(set_level)

    address = None
    if os.path.exists('/dev/log'):
        address = '/dev/log'
    elif os.path.exists('/var/run/syslog'):
        address = '/var/run/syslog'
    else:
        address = ('127.0.0.1', 514)
    # Add syslog handler before adding formatters
    root_logger.addHandler(
        SysLogHandler(address=address, facility=SysLogHandler.LOG_LOCAL0)
    )

    for handler in root_logger.handlers:
        handler.setFormatter(logging.Formatter(formatter))

    return config_log_int
