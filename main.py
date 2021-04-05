import csv
from datetime import datetime
from pprint import pformat
from lib.logger import logger
from utils.config_loader import ConfigLoader
from utils.raw_data_loader import DirectoryScanner
from utils.pixel_mapper import PixelMapper
from utils.fapar_calc import FaparCalc
from utils.model_draw import FaparModel


if __name__ == '__main__':
    config_name = 'config.yaml'
    logger.info('Parsing config {}'.format(config_name))
    config = ConfigLoader(config_name).parse_config()
    logger.debug(pformat(config))

    scanner = DirectoryScanner(config['workdir'])
    logger.debug(scanner.scenes)
    fapar_results = []
    for scene in scanner.scenes:
        mapp = PixelMapper(scanner.scenes[scene])
        if 'points' in config:
            for point in config['points']:
                rc = mapp.get_geo2raster(point[2:4])
                if rc:
                    b = FaparCalc(mapp.metadata, rc)
                    if b.mean == 0.0:
                        continue
                    fapar_results.append((point, scene, mapp.metadata['DATE_ACQUIRED'], b.DOY, b.mean, b.sd))
                    print(b.mean)
    #print(pformat(fapar_results))
    date_string = f'{datetime.now():%Y-%m-%d_%H:%M:%S%z}'
    with open('fapar_results_{}.csv'.format(date_string), 'w') as f:
        w = csv.writer(f)
        w.writerows(fapar_results)
    a = FaparModel(fapar_results)
    b = a.draw_model()


