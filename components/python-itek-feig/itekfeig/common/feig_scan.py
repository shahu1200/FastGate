"""
Feig SCAN mode.

.. TODO:: implementation
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..common.feig_base import FeigBase
#from ..common.feig_errors import FeigError

####################################################################################
####    SCAN MODE API
####
####    Format:-
####        COM_ADR + SEP + USR_HDR(1-4) + UID + SEP + DATA + END_USR(1-3)
####################################################################################


class FeigScan(FeigBase):
    def __init__(self, interface, lastError):
        """This class implements SCAN mode functionality of Feig reader.

        Args:
            interface: This the interface on which communication will happen.
            lastError: This parameter is shared for reporting error
        """
        # print("feig_scan.py class FeigScan init")
        super().__init__()

        FeigBase._interface = interface
        FeigBase._last_error = lastError
