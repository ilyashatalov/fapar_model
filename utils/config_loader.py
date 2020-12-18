import yaml
import sys
from lib.logger import logger


class ConfigLoader:

    def __init__(self, filename):
        configs = None
        with open(filename, 'r') as stream:
            try:
                configs = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                logger.error(exc)
                sys.exit('Config critical error')

        self.__config = {
            'workdir': configs['workdir'],
            'result_filename': configs['results_filename'],
            'points': configs['points'],
            'polygons': configs['polygons']
        }

    def parse_config(self):
        return self.__config

