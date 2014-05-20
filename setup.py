# -*- coding: utf-8 -*-
# Copyright (C) 2014, David Poulter
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
from setuptools import setup
from setuptools import find_packages


setup(name="consyn",
      description="A Concatenative synthesis command line tool",
      author="Dave Poulter",
      author_email="dapoulter@gmail.com",
      url="https://github.com/davebrent/consyn/",
      license="GNU/GPL version 3",
      version="0.0.1",
      packages=find_packages(),
      test_suite="nose.collector",
      entry_points="""
      [console_scripts]
      consyn = consyn.cli:main
      """,)
