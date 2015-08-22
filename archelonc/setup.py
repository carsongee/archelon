#!/usr/bin/env python
"""
Package installer for archelon client
"""
from __future__ import absolute_import
from setuptools import setup, find_packages


VERSION = __import__('archelonc').VERSION

with open('README.rst') as readme:
    README = readme.read()

setup(
    name='archelonc',
    version=VERSION,
    packages=find_packages(),
    package_data={},
    license='AGPLv3',
    author='Carson Gee',
    author_email='x@carsongee.com',
    url="http://github.com/carsongee/archelon",
    description=("Client connected to archelonc for Web shell history"),
    long_description=README,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Information Technology',
        ('License :: OSI Approved :: '
         'GNU Affero General Public License v3'),
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=[
        'npyscreen',
        'requests>=2.4.2',
        'six',
        ],
    scripts=['scripts/archelon'],
    entry_points={'console_scripts': [
        'archelonf = archelonc.command:search_form',
        'archelon_update = archelonc.command:update',
        'archelon_import = archelonc.command:import_history',
        'archelon_export = archelonc.command:export_history',
    ]},
    zip_safe=True,
)
