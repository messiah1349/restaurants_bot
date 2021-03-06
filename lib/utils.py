import datetime
import time
import yaml

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

STRFTIME = '%Y-%m-%d %H:%M:%S'

def read_file(file_name):
    with open(file_name, 'r') as file:
        query = file.read()

    return query


def read_config(config_path):
    with open(config_path, 'r') as file:
        prime_service = yaml.safe_load(file)

    return prime_service


def string_to_unix(date_str: str) -> int:
    return time.mktime(datetime.datetime.strptime(date_str, STRFTIME).timetuple())


def unix_to_string(date_unix:int) -> str:
    return datetime.datetime.utcfromtimestamp(date_unix).strftime(STRFTIME)
