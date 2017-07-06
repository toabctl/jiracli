# -*- coding: utf-8 -*-
#
# Copyright 2016 Thomas Bechtold <thomasbechtold@jpberlin.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import unittest

from ddt import ddt, data, unpack
import jiracli


@ddt
class BaseTest(unittest.TestCase):
    @data(
        ('closed', 'green'),
        ('CLOSED', 'green'),
        ('open', 'red'),
        ('Open', 'red'),
        ('in progress', 'yellow'),
        ('anything else', 'blue'),
    )
    @unpack
    def test_issue_status_color(self, status, expected_color):
        assert jiracli.issue_status_color(status) == expected_color
