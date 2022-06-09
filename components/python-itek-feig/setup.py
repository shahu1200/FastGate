#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os

from setuptools import setup, find_packages

# Package meta-data
NAME = 'itek_feig'

DESCRIPTION = 'Module for FEIG readers'
EMAIL = 'anishkumar.singh@infoteksoftware.com'
AUTHOR = 'anish kumar singh'

# Package repository link
URL = 'https://itekpune.visualstudio.com/Components/_git/python-itek-feig/'

# Packages (Dependency) Required For This Module
# also add this package name with version requirement in requirements.txt
REQUIRED = ['pyserial']

# Add Created Packages
# add folder name and find_packages will auto added all packages
PACKAGES = ['itekfeig', 'itekfeig.common', 'itekfeig.interface', 'itekfeig.readers']  # package directory name

# Add keywords related to module
KEYWORDS = 'feig uhf'

# Package license type
LICENSE = 'i-TEK License'

# ------------------------------------------------
# The rest you shouldn't have to touch too much :)
# ------------------------------------------------

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

# Load the package's version.py module as a dictionary.
here = os.path.join(here, 'itekfeig')

about = {}
with open(os.path.join(here, 'version.py')) as f:
    exec(f.read(), about) # pylint: disable=W0122

# Main setup works from here
setup(
    name=NAME,
    version=about['version'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    packages=find_packages(include=PACKAGES),
    #package_dir={'': PACKAGES},
    install_requires=REQUIRED,
    include_package_data=True,
    license=LICENSE,
    keywords=KEYWORDS,
    classifiers=[
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'License :: Other/Proprietary License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.5',
    platforms='any',
)
