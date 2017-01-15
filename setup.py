#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from setuptools import setup, find_packages

def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

here = os.path.abspath(os.path.dirname(__file__))

# put package test requirements here
requirements = [
    "uniplate==0.0.1",
    "pydbus==0.6.0",
    "pgi==0.0.11.1",
]

# put package test requirements here
test_requirements = [
    "hypothesis==3.6.1",
    "pytest==3.0.5"
]

setup(
    name='python-nstack-shim',
    version='0.0.1',
    description="Python NStack Shim",
    long_description="Allows calling Python-based container methods from NStack workflows with typed data",
    license='Apache',
    author="NStack",
    author_email='ed@nstack.com',
    url='https://github.com/nstackcom/python-nstack-shim',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", ""]),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'nstack-runner = nstack.runner:main',
        ],
    },
    install_requires=requirements,
    zip_safe=False,
    test_suite='tests',
    tests_require=test_requirements,
    keywords='nstack',
    platforms=['POSIX'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development',
        'Private :: Do Not Upload',  # hack to force invalid package for upload
    ],
)
