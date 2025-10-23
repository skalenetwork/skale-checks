#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (
    find_packages,
    setup,
)

extras_require = {
    'linter': [
        "ruff>=0.5.5"
    ],
    'dev': [
        "twine>=5.1.1"
    ],
}

extras_require['dev'] = (
    extras_require['linter'] + extras_require['dev']
)

setup(
    name='skale-checks',
    version='1.1',
    description='Checks for SKALE infrastructure',
    long_description_markdown_filename='README.md',
    author='SKALE Labs',
    author_email='support@skalelabs.com',
    url='https://github.com/skalenetwork/skale-checks',
    install_requires=[
        "skale.py>=7.6dev0,<8",
        "elasticsearch>=7.17.6,<8",  # Latest 7.x, compatible with Python 3.13 and ES 7.x
        "PyYAML==6.0.3"
    ],
    python_requires='>=3.12,<4',
    extras_require=extras_require,
    keywords=['skale', 'checks'],
    packages=find_packages(),
    package_data={
        'skale_checks': ['requirements.yaml']
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.12',
    ]
)
