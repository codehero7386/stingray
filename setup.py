#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

# NOTE: The configuration for the package, including the name, version, and
# other information are set in the setup.cfg file.

import os
import sys
from setuptools import setup

# Provide helpful messages for contributors running tests or building documentation.
TEST_HELP = """
Note: Running tests and building documentation has changed. Use the following commands:

To run tests:
    tox -e test

To build documentation:
    tox -e build_docs

For more information, see the development guide.
"""

if 'test' in sys.argv:
    print(TEST_HELP)
    sys.exit(1)

DOCS_HELP = """
Note: Building documentation has changed. Use the following commands:

To build documentation:
    tox -e build_docs

For more information, see the installation guide.
"""

if 'build_docs' in sys.argv or 'build_sphinx' in sys.argv:
    print(DOCS_HELP)
    sys.exit(1)

# Define a template for version retrieval.
VERSION_TEMPLATE = """
try:
    from setuptools_scm import get_version
    version = get_version(root='..', relative_to=__file__)
except Exception:
    version = '{version}'
""".lstrip()

# Use setuptools_scm to retrieve the version and write it to a version.py file.
setup(
    use_scm_version={
        'write_to': os.path.join('stingray', 'version.py'),
        'write_to_template': VERSION_TEMPLATE
    },
    name='your-package-name',  # Replace with your package name
    description='A short description of your package',
    long_description='A longer description of your package',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/your-package-name',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
        # List your package's dependencies here
        'numpy',
        'scipy',
    ],
    extras_require={
        'docs': ['sphinx'],
        'test': ['pytest'],
    },
    packages=['stingray'],  # Replace with your package name
    include_package_data=True,
)
