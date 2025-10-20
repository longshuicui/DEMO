# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/17 14:07
# @Author  : cuils
# @Description:
"""
import os
import datetime
import logging
from logging.handlers import RotatingFileHandler


HOME = os.environ.get("HOME", ".")


def get_logger(name) -> logging.Logger:
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    logdir = os.path.join(HOME, f".link_coder/{current_time}")
    os.makedirs(logdir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(levelname)s %(asctime)s [%(filename)s:%(lineno)s]>>> %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler = RotatingFileHandler(
        filename=os.path.join(logdir, f"link-coder.log"),
        backupCount=3,
        maxBytes=1024 * 1024 * 1024
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

