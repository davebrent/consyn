# -*- coding: utf-8 -*-
import os

from sqlalchemy import Float


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
BUFSIZE = 1024
HOPSIZE = 512
FEATURE_SLOTS = 33
FEATURE_TYPE = Float
DATABASE_PATH = os.path.join(ROOT_DIR, "consyn.sqlite")
DATABASE_URL = "sqlite:///{}".format(DATABASE_PATH)
DTYPE = "float32"
