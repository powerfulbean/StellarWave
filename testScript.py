# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 16:52:18 2019

@author: Jin Dou
"""

import DataIO
from DataIO import getFileList,saveObject
from DataStruct.RawData import CBitalinoRawdata
from DataStruct.LabelData import CVisualLabels
from DataStruct.DataSet import CDataOrganizor

dir_list = ['dirLabels','dirData']
oDir = DataIO.DirectoryConfig(dir_list,r".\GlsDataDirectory.conf")
oDir.checkFolders()
labelFiles = getFileList(oDir['dirLabels'],'.txt')
dataFiles = getFileList(oDir['dirData'],'.txt')

oRaw = CBitalinoRawdata()
oRaw.readFile(dataFiles[0])
oRaw.calTimeStamp()

oLabel = CVisualLabels()
oLabel.readFile(labelFiles[0])
oLabel.enhanceTimeStamps()

oDataOrganizor = CDataOrganizor(oRaw.numChannels,oRaw.sampleRate,oRaw.description['channelInfo'][1])
oDataOrganizor.addLabels(oLabel)
oDataOrganizor.assignTargetData([oRaw])

saveObject(oDataOrganizor.labels,r"./",'testOrganizor')
