#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os
import sys

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = "itekcsv"
DESCRIPTION = "To Export Database in CSV"
EMAIL = "sangam@ifaceconsulting.com"
AUTHOR = "Sangam Wavre"

# What packages are required for this module to be executed?
REQUIRED = []

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, "__version__.py")) as f:
    exec(f.read(), about)


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    py_modules=["database_to_csv"],
    install_requires=REQUIRED,
    include_package_data=True,
    license="itek",
    keywords="database csv",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    entry_points={
        "console_scripts": [
            "itekcsv=database_to_csv:main",
        ],
    },
    python_requires='>=3.5',
)
