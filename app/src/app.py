import logging
import os

import src.logging

logger = logging.getLogger(__name__)


def create_app():

    src.logging.init(__package__)



    return None  # TODO MRH return haystack


def get_project_root_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..")

