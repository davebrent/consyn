# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import find_packages


setup(name="consyn",
      description="A Concatenative synthesis command line tool",
      version="0.0.1",
      packages=find_packages(),
      entry_points="""
      [console_scripts]
      consyn = consyn.commands:main
      """,)
