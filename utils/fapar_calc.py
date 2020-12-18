import os
import sys
import re
import ntpath
import datetime
import csv
import numpy as np
import math
import yaml
import logging
import csv
from PIL import Image


class FaparCalc:
    imaarays = []
    mean = float()
    sd = float ()
    metadata = {}
    rc = []
    DOY = int()

    def __init__(self, metadata, rc):
        self.metadata = metadata
        self.rc = rc
        self.get_imaarays()
        self.__date_to_nth_day()
        self.get_mean_sd(self.fapar_calc(self.metadata, self.imaarays))

    def __date_to_nth_day(self):
        date = datetime.datetime.strptime(self.metadata['DATE_ACQUIRED'], '%Y-%m-%d')
        new_year_day = datetime.datetime(year=date.year, month=1, day=1)
        self.DOY = (date - new_year_day).days + 1

    def get_imaarays(self):
        '''return arrays with all neighbours of pixel (array 9x9)'''
        # subtract one cause python numbering from 0
        r = self.rc[0]-1
        c = self.rc[1]-1
        filepath_blue = Image.open(self.metadata['pics_dir']+'/'+self.metadata['FILE_NAME_BAND_1'].strip('\"'))
        filepath_red = Image.open(self.metadata['pics_dir']+'/'+self.metadata['FILE_NAME_BAND_3'].strip('\"'))
        filepath_ir = Image.open(self.metadata['pics_dir']+'/'+self.metadata['FILE_NAME_BAND_4'].strip('\"'))
        imarray_blue = np.array(filepath_blue)
        imarray_red = np.array(filepath_red)
        imarray_ir = np.array(filepath_ir)
        im_blue = []
        im_blue_s = []
        im_red = []
        im_red_s = []
        im_ir = []
        im_ir_s = []
        for i in [-1,0,+1]:
            im_blue_s = []
            im_ir_s = []
            im_red_s = []
            for j in [-1,0,+1]:
                im_blue_s.append(imarray_blue[r+i][c+j])
                im_red_s.append(imarray_red[r+i][c+j])
                im_ir_s.append(imarray_ir[r+i][c+j])
            im_blue.append(im_blue_s)
            im_red.append(im_red_s)
            im_ir.append(im_ir_s)
        self.imaarays = [np.array(im_blue), np.array(im_red), np.array(im_ir)]

    def fapar_calc(self, metadata, imarrays):
        solar_zen_ang = metadata['solar_zen_ang']
        sensor_zen_ang = metadata['sensor_zen_ang']
        rad_gain = metadata['rad_gain']
        rad_offset = metadata['rad_offset']
        sun_elevation = metadata['sun_elevation']
        sun_sen_rel_az = metadata['sun_sen_rel_az']
        k = metadata['k']
        pic = metadata['pic']
        hg = metadata['hg']
        E0 = metadata['E0']
        cosg = np.cos(solar_zen_ang) * np.cos(sensor_zen_ang) + np.sin(solar_zen_ang) * np.sin(sensor_zen_ang) * np.cos(sun_sen_rel_az)
        G = (np.tan(solar_zen_ang)**2 + np.tan(sensor_zen_ang)**2 - 2 * np.tan(solar_zen_ang) * np.tan(sensor_zen_ang) * np.cos(sun_sen_rel_az))**(1/2)
        b_blue = imarrays[0]
        b_red = imarrays[1]
        b_ir = imarrays[2]
    #    dsol = 1.0/((1.00014 - 0.01671*np.cos(2*np.pi*(0.9856002831*DOY - 3.4532868)/360)\
    #           -0.00014*np.cos(4*np.pi*(0.9856002831*DOY - 3.4532868)/360))*\
    #           (1.00014 - 0.01671*np.cos(2*np.pi*(0.9856002831*DOY - 3.4532868)/360)\
    #           -0.00014*np.cos(4*np.pi*(0.9856002831*DOY - 3.4532868)/360)))
        if 'dsol' in metadata.keys():
            dsol = metadata['dsol']
        else:
            dsol = (1.00014 - 0.01671*np.cos(2*np.pi*(0.9856002831*self.DOY - 3.4532868)/360)\
                   -0.00014*np.cos(4*np.pi*(0.9856002831*self.DOY - 3.4532868)/360))
        # First line filled by zeros for using numpy array
        z=[[0, 0.27505, 0.35511, -0.004, -0.322, 0.299, -0.0131, 0, 0, 0, 0, 0],
           [0, -10.036, -0.019804, 0.55438, 0.14108, 12.494, 0, 0, 0, 0, 0, 1],
           [0, 0.42720, 0.069884, -0.33771, 0.24690, -1.0821, -0.30401, -1.1024, -1.2596, -0.31949, -1.4864, 0]]
        l=np.array(z)
        rhot = []
        L70F_list = []
        for row in range(imarrays[0].shape[0]):
            for col in range(imarrays[0].shape[1]):
                pix_band = [b_blue[row, col], b_red[row, col], b_ir[row, col]]
                for i in range(3):
                    Rl = rad_gain[i] * pix_band[i] + rad_offset[i]
                    rho = (np.pi * Rl * dsol**2)/(E0[i]*np.cos(solar_zen_ang))
                    f1 = ((np.cos(solar_zen_ang) * np.cos(sensor_zen_ang))**(k[i] - 1))/\
                         (np.cos(solar_zen_ang) + np.cos(sensor_zen_ang))**(1 - k[i])
                    f2 = (1 - hg[i]**2)/(1 + 2 * hg[i]*cosg + hg[i]**2)**(3/2)
                    f3 = 1 + (1 - pic[i])/(1 + G)
                    F = f1 * f2 * f3
                    rhot.append(rho/F)
                g1 =((l[1,1] * (rhot[0] + l[1,2])**2) + (l[1,3] * (rhot[1] + l[1,4])**2) + l[1,5] * rhot[0] * rhot[1])/\
                     (l[1,6] * (rhot[0] + l[1,7])**2 + l[1,8] * (rhot[1] + l[1,9])**2 + l[1,10] * rhot[0] * rhot[1] + l[1,11])
                g2 =((l[2,1] * (rhot[0] + l[2,2])**2) + (l[2,3] * (rhot[2] + l[2,4])**2) + l[2,5] * rhot[0] * rhot[2])/\
                     (l[2,6] * (rhot[0] + l[2,7])**2 + l[2,8] * (rhot[2] + l[2,9])**2 + l[2,10] * rhot[0] * rhot[2] + l[2,11])
                L7OF = ((l[0,1] * g2) - l[0,2] * g1 - l[0,3])/\
                       ((l[0,4] - g1)**2 + (l[0,5] - g2)**2 + l[0,6])
                L70F_list.append(L7OF)
                rhot.clear()
        return np.array(L70F_list)

    def get_mean_sd(self, fapar_array):
        flatten_arr = fapar_array.flatten()
        flatten_arr = flatten_arr[(flatten_arr >= 0) & (flatten_arr <= 1)]
        if flatten_arr.size > 0:
            self.mean = np.mean(flatten_arr)
            self.sd = np.std(flatten_arr)
        else:
            logging.warning('No appropriate fapar for mean and sd')