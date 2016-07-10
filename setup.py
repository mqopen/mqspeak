#!/usr/bin/env python3
#
# Copyright (C) Ivo Slanina <ivo.slanina@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

import mqspeak

def readme():
    with open('readme.md') as f:
        return f.read()

setup(
    name = "mqspeak",
    url = mqspeak.__project_url__,
    version = mqspeak.__version__,
    packages = find_packages(exclude = ['doc']),
    install_requires = ['mqreceive>=0.1.1'],
    author = mqspeak.__author__,
    author_email = mqspeak.__email__,
    description = "MQTT bridge",
    long_description = readme(),
    license = "GPLv3",
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Customer Service',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Other Audience',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Communications',
        'Topic :: Home Automation',
        'Topic :: Internet',
    ],
    keywords = 'iot internetofthings mqopen mqtt sensors thingspeak phant',
    entry_points = {
        "console_scripts": [
            "mqspeak = mqspeak.__main__:main"
        ]
    }
)
