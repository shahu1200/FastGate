"""
i-Tek Feig UHF reader library
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .version import version

from .common.feig_logger import FeigLogger
from .common.feig_errors import FeigError

from .readers.LRU1002 import LRU1002
from .readers.HyWear import HyWear
from .readers.MRU102 import MRU102
from .readers.LRU500i import LRU500i

# from .gs1 import sgtin96_decoder
from .gs1 import sgtin96_to_ean
from .gs1 import tid_parser
from .gs1 import gtin_check

SUPPORTED_READERS = [
    "LRU1002",
    "MRU102",
    "MU02",
    "LRU500iPOE",
    "LRU500iBD",
    "HyWear",
]
"""List of supported readers."""

class ReaderNotSupportedError(Exception):
    """Reader Not Supported"""
    pass


def FeigReader(reader: str):
    """Returns reader object from given reader name.

    Args:
        reader: name of the reader in SUPPORTED_READERS

    Raises:
        ReaderNotSupportedError
    """
    if reader not in SUPPORTED_READERS:
        raise ReaderNotSupportedError

    if reader == "LRU1002":
        return LRU1002()

    if reader == "MRU102":
        return MRU102()

    if reader == "LRU500iPOE":
        return LRU500i("poe")

    if reader == "LRU500iBD":
        return LRU500i("bd")

    if reader == "HyWear":
        return HyWear()


__all__ = [
    "version",
    "SUPPORTED_READERS",
    "FeigReader",
    "FeigLogger",
    "FeigError",
    "LRU1002",
    "HyWear",
    "MRU102",
    "LRU500i",
    #'sgtin96_decoder',
    "tid_parser",
    "sgtin96_to_ean",
    "gtin_check",
]
