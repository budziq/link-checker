#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
import codecs
from os import path
import re

here = path.abspath(path.dirname(__file__))

def read(*parts):
    with codecs.open(path.join(here, *parts), 'r', encoding='utf-8') as filep:
        return filep.read()

def find_version(*paths):
    version_file = read(*paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='link-checker',
    version=find_version("checker.py"),

    description='A simple link checker intended mostly for CI usage',
    long_description=read("README.md"),
    long_description_content_type='text/markdown',

    url='https://github.com/budziq/link-checker',
    author='Michał Budzyński',
    author_email='budziq@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='links link-checker CI HTML',

    py_modules=['checker'],
    install_requires=[
        'click>=6.7',
        'requests>=2.18',
        'beautifulsoup4>=4.6',
    ],
    entry_points='''
        [console_scripts]
        link-checker=checker:check
    ''',
    project_urls={
        'Bug Reports': 'https://github.com/budziq/link-checker/issues',
        'Source': 'https://github.com/budziq/link-checker',
    },
)
