#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (
    find_packages,
    setup,
)

setup(
    name='skale-checks',
    version='1.0.0',
    description='Checks for SKALE infrastructure',
    long_description_markdown_filename='README.md',
    author='SKALE Labs',
    author_email='support@skalelabs.com',
    url='https://github.com/skalenetwork/skale-checks',
    install_requires=[
        "skale.py == 5.1dev5",
        "elasticsearch == 7.12.0"
    ],

    python_requires='>=3.7,<4',

    keywords=['skale', 'checks'],
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
    ]
)