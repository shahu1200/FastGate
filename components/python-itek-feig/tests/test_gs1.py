#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

from itekfeig.gs1 import *

def test_gtin_check():
    # EAN-13
    assert(gtin_check("8905263687765") == True)
    assert(gtin_check("8905263078990") == True)
    assert(gtin_check("8905263078999") == False)
    # EAN-8
    assert(gtin_check("") == False)
    assert(gtin_check("96385074") == True)

def test_sgtin96_to_ean():
    assert(sgtin96_to_ean("30361fad281e5557487b6d45") == ("8907594310619", "100000296261"))

    with pytest.raises(SGTINDecodeError):
        assert(sgtin96_to_ean("00361fad281e5557487b6d45"))
