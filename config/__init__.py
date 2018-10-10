import configparser
import os
import logging

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '../config.ini')

config = configparser.ConfigParser()
config.read_file(open(filename))

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)