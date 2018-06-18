#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""The setup script.
py setup.py bdist_wheel -d wheel --> saves wheel to folder, the folder must include a __init__.py
conda build ..\hkfunctions --> build conda package
"""

from setuptools import setup, find_packages

requirements = []
extras_require = {
    "sqlserver": ["pymssql"],
    "sybase": ["sqlanydb"],
    "log": ["pymssql"],
    "files": ["xlrd", "openpyxl"]
}

setup(
    name='hkfunctions',
    version='0.7.1',
    description="function library",
    long_description='',
    author="Henric Sundberg",
    author_email='henric.sundberg@hultsfred.se',
    url='',
    packages=['hkfunctions'],
    include_package_data=True,
    install_requires=requirements,
    extras_require=extras_require,
    license="MIT license",
    zip_safe=False,
    keywords='hkfunctions',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
)
