#!/usr/bin/env python
"""
Package installer for archelon client
"""

from setuptools import setup, find_packages


VERSION = __import__('archelond').VERSION

with open('README.rst') as readme:
    README = readme.read()

setup(
    name='archelond',
    version=VERSION,
    packages=find_packages(),
    include_package_data=True,
    license='AGPLv3',
    author='Carson Gee',
    author_email='x@carsongee.com',
    url="http://github.com/carsongee/archelon",
    description=("Web server for Web shell history"),
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
        'flask',
        'flask-htpasswd>=0.3.0',
        'uwsgi',
        'pytz',
        'six',
        'elasticsearch',
        'Flask-Assets',
        'cssmin',
        'jsmin',
        ],
    entry_points={'console_scripts': [
        'archelond = archelond.web:run_server',
    ]},
    zip_safe=False,
)
