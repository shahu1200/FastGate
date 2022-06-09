#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import logging.handlers as handlers
import os

LOG_FILE_NAME = "itekfeiglib.log"


def FeigLogger(loggerName=None, loggerPath=None, loggerLevel=None):
    """Create logger instance.

    Args:
        loggerName: str or None, None = root logger
        loggerPath: str => path of the logger file, Defaults to $HOME directory
        loggerLevel: int or 'logging' module log levels, Defaults to logging.NOTSET

    Returns:
        logger: object
    """

    # If path is empty, log to home directory
    if loggerPath is None:
        # for python 3.5+
        from pathlib import Path

        loggerPath = str(Path.home())
    loggerPath = os.path.join(loggerPath, LOG_FILE_NAME)

    logger = logging.getLogger(loggerName)

    # Set Log level
    level = logging.NOTSET  # Default
    if isinstance(loggerLevel, int):
        if loggerLevel == logging.CRITICAL:
            level = logging.CRITICAL

        elif loggerLevel == logging.ERROR:
            level = logging.ERROR

        elif loggerLevel == logging.WARNING:
            level = logging.WARNING

        elif loggerLevel == logging.INFO:
            level = logging.INFO

        elif loggerLevel == logging.DEBUG:
            level = logging.DEBUG
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s::%(levelname)s::%(name)s::%(message)s")

    # timed logger
    timedHandler = handlers.TimedRotatingFileHandler(
        loggerPath, when="midnight", interval=1, backupCount=5,
    )
    timedHandler.setFormatter(formatter)
    logger.addHandler(timedHandler)

    # stream logger
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger
