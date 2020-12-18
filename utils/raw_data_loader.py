import os
import re
import csv
import pyproj
import math
import numpy as np
from lib.logger import logger

# Some working with directories
class DirectoryScanner:
    dirmtl_list = []
    mtl_regex = '.*MTL.*.txt'
    scenes = {} # List of dicts with full path as key and metadata dict as value

    def __init__(self, dir_path):
        dirs_with_mtl = self.__get_subdirs(dir_path)
        for dir in dirs_with_mtl:
            self.scenes[dir] = self.parse_mtl_file(dir)

    def __get_subdirs(self, dir_path):
        # Get subdirs of dir_path with scenes
        dirs_with_mtl = []
        dirs = os.listdir(dir_path)
        for dirname in dirs:
            if os.path.isdir(dir_path + '/' + dirname):
                files = os.listdir(dir_path + '/' + dirname)
            else:
                continue
            for filename in files:
                if re.match('.*MTL.*.txt', filename):
                    dirs_with_mtl.append(dir_path + '/'+ dirname)
                    break
        return dirs_with_mtl

    def __find_mtl(self, dir_path):
        files = os.listdir(dir_path)
        for file in files:
            if re.search(self.mtl_regex, file):
                return file
        return None

    def parse_mtl_file(self, datadir):
        """
        Set metadata from scene
        """
        metadata = {}
        mtl_file = self.__find_mtl(datadir)
        with open(datadir + '/' + mtl_file, "r", encoding='utf-8', newline='') as csvfile:
            mtl = csv.reader(csvfile, delimiter='=')
            try:
                for row in mtl:
                    try:
                        metadata.update({row[0].strip(): row[1].strip()})
                    except IndexError:
                        logger.warning('no value for ' + row[0])
                        pass
            except csv.Error as e:
                logger.warning(e)
        # IMPORT IMAGE DATA
        metadata['pics_dir'] = datadir
        metadata['samples'] = float(metadata['REFLECTIVE_SAMPLES'])
        metadata['lines'] = float(metadata['REFLECTIVE_LINES'])
        ul_lat = float(metadata['CORNER_UL_LAT_PRODUCT'])
        ul_lon = float(metadata['CORNER_UL_LON_PRODUCT'])
        ur_lat = float(metadata['CORNER_UR_LAT_PRODUCT'])
        ur_lon = float(metadata['CORNER_UR_LON_PRODUCT'])
        ll_lat = float(metadata['CORNER_LL_LAT_PRODUCT'])
        ll_lon = float(metadata['CORNER_LL_LON_PRODUCT'])
        lr_lat = float(metadata['CORNER_LR_LAT_PRODUCT'])
        lr_lon = float(metadata['CORNER_LR_LON_PRODUCT'])

        metadata['ll_corners'] = np.array([
            [ul_lat, ul_lon, 0],
            [ur_lat, ur_lon, 0],
            [lr_lat, lr_lon, 0],
            [ll_lat, ll_lon, 0]])

        metadata['ecef'] = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
        metadata['lla'] = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')

        x, y, z = pyproj.transform(metadata['lla'], metadata['ecef'],
                                   metadata['ll_corners'][:, 1],
                                   metadata['ll_corners'][:, 0],
                                   metadata['ll_corners'][:, 2], radians=False)
        metadata['eta_corners'] = np.array([x, y, z]).T

        # get mean coords cause satellite near center ofpicture
        ll_c_mean = list(np.mean(metadata['ll_corners'][:, 0:2],
                                 axis=0))  # get mean coords cause sattelite near center ofpicture
        ll_c_mean.append(7e5)
        ll_sat = np.array(ll_c_mean)
        x2, y2, z2 = pyproj.transform(metadata['lla'], metadata['ecef'], ll_sat[1], ll_sat[0], ll_sat[2],
                                      radians=False)
        metadata['eta_sat'] = np.array([x2, y2, z2])
        metadata['va'] = metadata['eta_corners'][1, :] - metadata['eta_corners'][0, :]
        metadata['vb'] = metadata['eta_corners'][2, :] - metadata['eta_corners'][0, :]
        metadata['vc'] = metadata['eta_corners'][3, :] - metadata['eta_corners'][0, :]
        va = metadata['va']
        vc = metadata['vc']
        metadata['s_alt'] = 710e3  # CARE HARDCODED ALT
        metadata['vs'] = (va + vc) / 2 - metadata['s_alt'] * np.cross(va, vc) / np.linalg.norm(np.cross(va, vc))

        # FAPAR METADATA
        metadata['rad_gain'] = [float(metadata['RADIANCE_MULT_BAND_1']), float(metadata['RADIANCE_MULT_BAND_3']), float(metadata['RADIANCE_MULT_BAND_4'])]
        metadata['rad_offset'] = [float(metadata['RADIANCE_ADD_BAND_1']), float(metadata['RADIANCE_ADD_BAND_3']), float(metadata['RADIANCE_ADD_BAND_4'])]
        try:
            metadata['dsol'] = float(metadata['EARTH_SUN_DISTANCE'])
        except KeyError as e:
            logger.warning('Keyerror at {}'.format(e))
        metadata['sun_elevation'] = math.radians(float(metadata['SUN_ELEVATION']))
        metadata['solar_zen_ang'] = math.radians(90 - float(metadata['SUN_ELEVATION']))
        metadata['sensor_zen_ang'] = math.radians(0) # ATTENTION!!!
        metadata['sun_sen_rel_az'] = math.radians(float(metadata['SUN_AZIMUTH']))

        # CONSTS
        metadata['k'] = [0.63931,0.81037, 0.76611]
        metadata['pic'] = [0.80760, 0.89472, 0.643]
        metadata['hg'] = [-0.06156, -0.03924, -0.10055]
        metadata['E0'] = [1969, 1551, 1044]
        return metadata
