# -*- coding: utf-8 -*-
#
# Copyright 2017 Thomas Bechtold <thomasbechtold@jpberlin.de>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import getpass
import os

from six.moves import configparser
from six.moves import input


def _config_credentials_get():
    """get username, password and url"""
    user = input("username:")
    password = getpass.getpass()
    url = input("url:")
    return user, password, url


def config_get(config_path):
    """get the configuration"""
    conf = configparser.RawConfigParser()
    conf.read([config_path])
    section_name = "defaults"
    if not conf.has_section(section_name):
        user, password, url = _config_credentials_get()
        conf.add_section(section_name)
        conf.set(section_name, "user", user)
        conf.set(section_name, "password", password)
        conf.set(section_name, "url", url)
        with os.fdopen(os.open(
                config_path, os.O_WRONLY | os.O_CREAT, 0o600), 'w') as f:
            conf.write(f)

    # some people prefer to not store the password on disk, so
    # ask every time for the password
    if not conf.has_option(section_name, "password"):
        password = getpass.getpass()
        conf.set(section_name, "password", password)

    # some optional configuration options
    if not conf.has_option(section_name, "verify"):
        conf.set(section_name, "verify", "true")

    return conf
