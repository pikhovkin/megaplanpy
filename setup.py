#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

setup(
    name='megaplanpy',
    version=__import__('megaplanpy').__version__,
    description=read('DESCRIPTION'),
    license='MIT',
    keywords='megaplan api',
    author='Sergey Pikhovkin',
    author_email='s@pikhovkin.ru',
    maintainer='Sergey Pikhovkin',
    maintainer_email='s@pikhovkin.ru',
    url='https://github.com/pikhovkin/megaplanpy/',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Environment :: Web Environment',
        'Natural Language :: Russian',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[],
    include_package_data=True,
    zip_safe=False,
    long_description=read('README.rst'),
    packages=find_packages()
)

