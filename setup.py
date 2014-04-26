# -*- coding: utf-8 -*-
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
