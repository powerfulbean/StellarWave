# -*- coding: utf-8 -*-
"""
Created on Sat Aug 31 01:26:24 2019

@author: Jin Dou
"""
import os
from abc import abstractmethod,ABC

from .. import outsideLibInterfaces as outLib
from ..DataIO import checkFolder, getFileName
from ..Helper.Cache import CStimuliCache
from .RawData import CData
from .StimuliData import CStimuli,CAuditoryStimuli


class CLabels(CData): 
    # for labels created by psychopy, the last number is microsecond but not millisecond 
    def __init__(self):
        super(CLabels, self).__init__()
        self.startTime = None
    
    def writeInfoForMatlab(self,folder):
        import json
        ans = dict()
        ans["startDate"] = str(self.startTime)
        dataDict = dict()
        cnt = 0
        for i in self.timestamps:
            s,e = i.getLabelDict() # get start and end event time
            dataDict[str(cnt)] = s
            cnt+=1
            dataDict[str(cnt)] = e
            cnt+=1 
        ans["labels"] = dataDict
        app_json = json.dumps(ans)
        #print(app_json)
        checkFolder(folder)
        fileAddress = str(folder) + self.description+"_labels_" + str(self.startTime).replace(":","-") + ".jin" 
        f = open(fileAddress,'w+')
        f.write(app_json)
        f.close
    
    def stimuliEventParser(self,buffer, stimuliStartTag, StimuliEndTag, i, recordObject):
        stimuliStart = buffer[i]
        if(stimuliStart[0] == stimuliStartTag):
            temp = stimuliStart[1]
            realName = temp
            recordObject.name = realName
            datetime = outLib._OutsideLibTime()._importDatetime() 
            
            temp = stimuliStart[2:len(stimuliStart)] # calculate start time
            [h,m,s,ms] = [int(t) for t in temp]
            startTime = datetime.time(h,m,s,ms)
            recordObject.startTime = startTime
            i+=1
            
            stimuliEnd = buffer[i]
            #the audio End Label
            if(stimuliEnd[0] == StimuliEndTag):
                recordObject.index = stimuliEnd[1]
                temp = stimuliEnd[2:len(stimuliEnd)] # calculate end time
                [h,m,s,ms] = [int(t) for t in temp]
                endTime = datetime.time(h,m,s,ms)
                recordObject.endTime = endTime
                i+=1
            else:
                print("visuallabels, parser error")
        else:
            print("visuallabels, parser error")
        
        return i, recordObject

    def writeType(self,typeName):
        for i in self.timestamps:
            i.type = typeName
            
    def enhanceTimeStamps(self):
        '''
        make the self.timestamps be independent from self.rawdata
        change the datetime.time (doesn't contain information of year,month,day) object into datetime.datetime object
        if applicatable, allocat rawdata to CLabelInfoCoarse.stimuli
        
        '''
        datetime = outLib._OutsideLibTime()._importDatetime()
        if(len(self.timestamps) != len(self.rawdata)):
            print("label warning: the number of rawdata is wrong, ",len(self.timestamps),' ',len(self.rawdata))
            #length of raw data is: ", len(self.rawdata))
        for i,labelInfo in enumerate(self.timestamps):
            if (i<len(self.rawdata)):
                labelInfo.promote(datetime,self.startTime.date(),self.rawdata[i]) #allocate rawdata to 
            else:
                labelInfo.promoteTime(datetime,self.startTime.date())
    
    @abstractmethod
    def readFile(self,fileName):
        return
    
    @abstractmethod
    def loadStimuli(self,Folder, extension, oCache : CStimuliCache = None):
        ''' 
        load stimuli in self.timestamps(CLabelInfoCoarse).stimuli
        '''
        pass

class CVisualLabels(CLabels):
    
    def readFile(self,fileName, readStimuli = False, stimuliDir = None):
        ''' 
        read all the necessary information from the label files
        
        '''
        #include the OutsideLib module for Input/Output
        self.outLibIO = outLib._OutsideLibIO()
        self.description = 'Visual'
        self.type = "Visual"
        buffer = []
        datetime = outLib._OutsideLibTime()._importDatetime()    
        
        with open(fileName, 'r') as the_file: #opoen the labels file
            lines = the_file.readlines()
        
        for line in lines: # read the label file
            temp = line.split()
            buffer.append(temp)
            
        i = 0
        while( i < len(buffer)): #buffer is the whole document
            #the first line, save the start date
            if(i == 0):
                [a,b,c,d,e,f] = [int(j) for j in buffer[i] if (j != '-' and j != ':') ]
                self.startTime = datetime.datetime(a,b,c,d,e,f) # Lib: datetime
                i+=1
                
            if(buffer[i][0] == 'First' or buffer[i][0] == 'Second' or buffer[i][0] == 'Cat' ):
                stimuliIdx = 0
                if(buffer[i][0] == 'First'):
                    stimuliIdx = 1
                elif( buffer[i][0] == 'Second'):
                    stimuliIdx = 2
                elif(buffer[i][0] == 'Cat'):
                    stimuliIdx = 0
                else:
                    stimuliIdx = -1
                i+=1
                                 
                while(buffer[i][0] == 'sub'):
                    tempRecord = CLabelInfoCoarse('','','','') #store crossing time
                    tempRecord2 = CLabelInfoCoarse('','','','') #store stimuli time
                    tempRecord3 = CLabelInfoCoarse('','','','') #store rest time
                    
                    i+=1
                    
                    if(buffer[i][0] == 'attendStart'):
                        i,tempRecord = self.stimuliEventParser(buffer,'attendStart','attendEnd',i,tempRecord)
                    elif(buffer[i][0] == 'unattendStart'):
                        i,tempRecord = self.stimuliEventParser(buffer,'unattendStart','unattendEnd',i,tempRecord)
                    elif(buffer[i][0] == 'crossingStart'):
                        i,tempRecord = self.stimuliEventParser(buffer,'crossingStart','crossingEnd',i,tempRecord)
                    else:
                        raise Exception("don't recognize the type "+ str(buffer[i][0])+' please check the file')
                    i,tempRecord2 = self.stimuliEventParser(buffer,'imageStart','imageEnd',i,tempRecord2)
                    i,tempRecord3 = self.stimuliEventParser(buffer,'restStart','restEnd',i,tempRecord3)
                    
                    tempName,t = os.path.splitext(tempRecord2.name)
                    tempRecord3.name = tempName + '_' + 'imagination' 
                    tempRecord.type = 'cross'
                    tempRecord2.type = 'image'
                    tempRecord3.type = 'rest'
                
                    self.timestamps.append(tempRecord)
                    self.rawdata.append('crossing')
                    self.timestamps.append(tempRecord2)
                    self.rawdata.append(str(stimuliIdx))
                    self.timestamps.append(tempRecord3)
                    self.rawdata.append('rest')
                    
            elif(buffer[i][0]=='-1'):
                break
            
            else:
                print("visuallabels, readFile error")
                return
            
    def loadStimuli(self,Folder, extension, oCache : CStimuliCache = None):
        ''' 
        load stimuli in self.timestamps(CLabelInfoCoarse).stimuli
        '''
        pass
        
class CBlinksCaliLabels(CLabels):
    
    def readFile(self, fileName):
        self.outLibIO = outLib._OutsideLibIO()
        tempName= getFileName(fileName)
        self.description = 'BlinksCali_' + tempName
        self.type = "BlinksCali"
        buffer = []
        with open(fileName, 'r') as the_file: #opoen the labels file
            lines = the_file.readlines()
        
        for line in lines: # read the label file
            temp = line.split()
            buffer.append(temp)
            
        i = 0
        self.startTime = self.parseTimeString(buffer[i][1] + ' ' + buffer[i][2])
        while( i < len(buffer)): #buffer is the whole document
            tempRecord = CLabelInfoCoarse('','','','') #store crossing time
            #the first line, save the start date
            Type = buffer[i][0]
            if(Type == 'blink' or Type == 'lookLeft' or Type == 'lookRight'):
                tempRecord.type = 'cali'
                if(buffer[i][0] == 'blink'):
                    tempRecord.name = 'blink'
                elif(buffer[i][0] == 'lookLeft'):
                    tempRecord.name = 'lookLeft'
                elif(buffer[i][0] == 'lookRight'):
                    tempRecord.name = 'lookRight'
                time = self.parseTimeString(buffer[i][1] + ' ' + buffer[i][2]).time() #read as datetime and change to time
                tempRecord.startTime = time
                tempRecord.endTime = time
                tempRecord.type = 'cali'
                self.timestamps.append(tempRecord)
                self.rawdata.append(self.description + '_' + Type)
                i += 1
            else:
                print("BlinksCaliLabels, readFile error")
                return
        
    def parseTimeString(self,string):
        dateTime = outLib._OutsideLibTime()._importDatetime() 
        return dateTime.datetime.strptime(string , '%Y-%m-%d %H:%M:%S.%f')
    
class CAuditoryLabels(CLabels):       
    
    def readFile(self,fileName):
        ''' 
        read all the necessary information from the label files
        '''
        #include the OutsideLib module for Input/Output
        self.outLibIO = outLib._OutsideLibIO()
        self.description = 'Auditory'
        self.type = "Auditory"
        buffer = []
        datetime = outLib._OutsideLibTime()._importDatetime()    
        
        with open(fileName, 'r') as the_file: #opoen the labels file
            lines = the_file.readlines()
        
        for line in lines: # read the label file
            temp = line.split()
            buffer.append(temp)
#        print(len(buffer))
        i = 0
        while( i < len(buffer)): #buffer is the whole document
#            print("i="+str(i))
#            print(buffer[i][0])
            
            #the first line, save the start date
            if(i == 0):
                [a,b,c,d,e,f] = [int(j) for j in buffer[i] if (j != '-' and j != ':') ]
                self.startTime = datetime.datetime(a,b,c,d,e,f) # Lib: datetime
                i+=1
            
            #the left/right label
            if(buffer[i][0]=='left' or buffer[i][0]=='right' or buffer[i][0] == 'Single'):
                
                leftflag = ''
                singleflag = False
                if(buffer[i][0] == 'left'):
                    leftflag = True
                elif(buffer[i][0] == 'Single'):
                    singleflag = True
                else:
                    leftflag = False
                
                tempRecord = CLabelInfoCoarse('','','','')
                
                i += 1
                audioStart = buffer[i]
                
                #the audio Start Label
                if(audioStart[0] == 'audioStart'):
                    # real audio name    
                    temp = audioStart[1] 
                    realName, extension = os.path.splitext(temp)
                    
                    if(singleflag == False):
                        # stimuli name
                        stimuliName = self.stimuliname(leftflag, realName)
                        tempRecord.name = stimuliName
                        #print(stimuliName)
                        otherstimulisName = self.stimuliname(not leftflag, realName)# other stimuli name
                        tempRecord.otherNames.append(otherstimulisName)
                        #print(otherstimulisName)
                    else:
                        tempRecord.name = realName
                        tempRecord.otherNames.append(realName)
                    
                    # calculate start time
                    temp = audioStart[2:len(audioStart)] 
                    [h,m,s,ms] = [int(t) for t in temp]
                    startTime = datetime.time(h,m,s,ms)
                    tempRecord.startTime = startTime
                    i+=1
                    
                    #the audio End Label
                    audioEnd = buffer[i]
                    if(audioEnd[0] == 'audioEnd'):
                        tempRecord.index = audioEnd[1]
                        temp = audioEnd[2:len(audioEnd)]
                        [h,m,s,ms] = [int(t) for t in temp]
                        endTime = datetime.time(h,m,s,ms)
                        tempRecord.endTime = endTime
                
                tempRecord.type = 'auditory'
                self.timestamps.append(tempRecord)
                i+=1
            elif(buffer[i][0]=='-1'):
                break
            else:
                raise TypeError("labels, loadfile error", buffer[i][0])
        
        self.writeType("auditory")              
        return buffer        

    
    def stimuliname(self,isLeft, realName):
        idx = realName.find('R')
        if(isLeft == True):
            realStimuli = realName[1:idx] # don't include the 'L'
        else:
            realStimuli = realName[idx+1:len(realName)] # don't include the 'R'
        return realStimuli    
    
    def loadStimuli(self,Folder, extension, oCache : CStimuliCache = None):
        ''' 
        load stimuli in self.timestamps(CLabelInfoCoarse).stimuli
        '''
        if(extension == '.wav'):
            for i in range(len(self.timestamps)):
                label = self.timestamps[i]
                mainStreamName = label.name
                otherStreamNames = label.otherNames
                print("AuditoryLabels, readStimuli:", mainStreamName,otherStreamNames[0])
                stimuliObject = CAuditoryStimuli()
                mainStreamFullPath = Folder + mainStreamName + extension
                otherStreamFullPaths = [Folder + i + extension for i in otherStreamNames]
                stimuliObject.loadStimulus(mainStreamFullPath,otherStreamFullPaths)
                # save this auditoryStimuli object to the data attribute of this markerRecord object
                self.rawdata.append(stimuliObject)
        
        elif(extension == 'cache'):
            for i in range(len(self.timestamps)):
                label = self.timestamps[i]
                mainStreamName = label.name
                otherStreamNames = label.otherNames
                print("AuditoryLabels, read Stimuli from cache:", mainStreamName,otherStreamNames[0])
                stimuliObject = CAuditoryStimuli()
                stimuliObject.loadStimulus(mainStreamName,otherStreamNames,oCache)                    
                # save this auditoryStimuli object to the data attribute of this markerRecord object
                self.rawdata.append(stimuliObject)
                
class CLabelInfoBase:
    pass
    
class CFGetLabelDict(ABC):
    
    def __init__(self):
        self._startInfoDict = None
        self._endInfoDict = None
        self._type = None
    
    def __call__(self,oLabelInfo:CLabelInfoBase):
        err = self.handle(oLabelInfo)
        if (err != 0 ):
            raise ValueError('Handle face problem with error code:' + str(err))
        if (self._check() == False):
            raise ValueError('At least one of the attributes is None,\
                             Please check the CFGetLabelDict.handle function')
        return self.startInfoDict, self.endInfoDict
    
    @abstractmethod
    def handle(self,oLabelInfo:CLabelInfoBase):
        return 0
    
    @property
    def startInfoDict(self):
        return self._startInfoDict.copy()
    
    @property
    def endInfoDict(self):
        return self._endInfoDict.copy()
    
    @property
    def labelType(self):
        return self._type.copy()
    
    def _check(self):
        if (type(self._type) == None):
            return False
        if (type(self._startInfoDict) == None):
            return False
        if (type(self._endInfoDict) == None):
            return False
        return True

class CLabelInfo(CLabelInfoBase):
    
    def __init__(self,desc,index):
        self.name = desc
        self.index = index
        self.type = ''
        self.startTime ='' #datetime.time or datetime.datetime object
        self.endTime = '' #dateime.time or datetime.datetime object 
    
    def getLabelDict(self,handle:CFGetLabelDict=None):
        if (self.type == 'attention') :
            name = self.name 
        elif (self.type == 'image' or self.type == 'rest' or self.type == 'cross'):
            name = self.name
        elif (self.type == 'cali'):
            name = self.name
        elif (self.type == 'auditory'):
            name = self.name + '_n_' + self.otherNames[0]
        else:
            name = self.name[self.name.find('-')+1:len(self.name)]
            name = self.name[0:self.name.find('_')]
        dict1 = {
                'name':name+'_Start',
                'time':str(self.startTime),
                }
        
        dict2 = {
                'name':name+'_End',
                'time':str(self.endTime),
                }
        return dict1,dict2

class CLabelInfoGeneral(CLabelInfo):
    ''' Time non-related CLabelInfo Type'''
    ''' It is used for recording general information of timestamps '''
    ''' Doesn't include stimuli data'''
    
    def __init__(self,desc,index,labelClassList):
        super(CLabelInfoGeneral, self).__init__(desc,index)
        self.labelClassList = labelClassList
        
    def __call__(self,query):
        if(type(query) == int):
            if(query >= 0 and query < len(self.labelClassList)):
                return self.labelClassList[query]
        elif(len(query) == len(self.labelClassList)):
            if(type(query[0]) == int):
                if( max(query) <= 1 and min(query) >= 0):
                    ans = list()
                    for idx, className in enumerate(self.labelClassList):
                        if(query[idx] == 1):
                            ans.append(className)
                    return ans
        
        raise ValueError("Query's value is not valid")
	
class CLabelInfoCoarse(CLabelInfo):
    ''' Time related CLabelInfo Type, but the time indicator is coarse'''
    ''' class to store information for a label marker, including:
        1. label name
        2. other useful label names
        3. start and end time
        4. label type
        5. label value: actual stimuli
    '''
    def __init__(self,name,index,startTime,endTime):
        super(CLabelInfoCoarse, self).__init__(name,index)
        self.otherNames = list() # background stimuli name
        self._promoteFlag = False
        self._promoteTimeFlag = False
        self.startTime = startTime #datetime.time or datetime.datetime object
        self.endTime = endTime #dateime.time or datetime.datetime object 
        self.stimuli = '' #label info (such as auditoryStimuli object)
        
    def getDuration_s(self):
        temp = self.endTime - self.startTime
        return temp.total_seconds()
        
    def checkPromoto(self,):
        return self._promoteFlag
    
    def promote(self,datetimeModule,dateObject, data):
        ''' 
        promote this CLabelInfoCoarse with absolute time, 
        and label data (such as image name for visual stimuli, and auditoryStimuli for auditory stimuli)
        
        '''
        if(self._promoteFlag == True):
            print("marker has been promoted")
        else:
            self.promoteTime(datetimeModule,dateObject)    
            self.stimuli = data
            self._promoteFlag = True
    
    def promoteTime(self,datetimeModule,dateObject):
        if(self._promoteTimeFlag == True):
            print("time of the marker has been promoted")
        else:
            startTime = datetimeModule.datetime(1,1,1,1,1,1)
            endTime = datetimeModule.datetime(1,1,1,1,1,1)
            self.startTime = startTime.combine(dateObject, self.startTime)
            self.endTime = endTime.combine(dateObject, self.endTime)
            self._promoteTimeFlag = True
    
    def sorted_key(self,x):
        return x.startTime


# class CLabelInfoCoarse:
    # ''' class to store information for a label marker, including:
        # 1. label name
        # 2. other useful label names
        # 3. start and end time
        # 4. label type
        # 5. label value: actual stimuli
    # '''
    # def __init__(self,name,index,startTime,endTime):
        # self.name = name
        # self.otherNames = list() # background stimuli name
        # self.index = index
        # self.startTime = startTime #datetime.time or datetime.datetime object
        # self.endTime = endTime #dateime.time or datetime.datetime object 
        # self.type = ''
        # self._promoteFlag = False
        # self._promoteTimeFlag = False
        # self.stimuli = '' #label info (such as auditoryStimuli object)
        
    # def getDuration_s(self):
        # temp = self.endTime - self.startTime
        # return temp.total_seconds()
        
    # def getLabelDict(self,type = None, handle=None):
        # if (self.type == 'attention') :
            # name = self.name 
        # elif (self.type == 'image' or self.type == 'rest' or self.type == 'cross'):
            # name = self.name
        # elif (self.type == 'cali'):
            # name = self.name
        # elif (self.type == 'auditory'):
            # name = self.name + '_n_' + self.otherNames[0]
        # else:
            # name = self.name[self.name.find('-')+1:len(self.name)]
            # name = self.name[0:self.name.find('_')]
        # dict1 = {
                # 'name':name+'_Start',
                # 'time':str(self.startTime),
                # }
        
        # dict2 = {
                # 'name':name+'_End',
                # 'time':str(self.endTime),
                # }
        # return dict1,dict2
    
    # def checkPromoto(self,):
        # return self._promoteFlag
    
    # def promote(self,datetimeModule,dateObject, data):
        # ''' 
        # promote this CLabelInfoCoarse with absolute time, 
        # and label data (such as image name for visual stimuli, and auditoryStimuli for auditory stimuli)
        
        # '''
        # if(self._promoteFlag == True):
            # print("marker has been promoted")
        # else:
            # self.promoteTime(datetimeModule,dateObject)    
            # self.stimuli = data
            # self._promoteFlag = True
    
    # def promoteTime(self,datetimeModule,dateObject):
        # if(self._promoteTimeFlag == True):
            # print("time of the marker has been promoted")
        # else:
            # startTime = datetimeModule.datetime(1,1,1,1,1,1)
            # endTime = datetimeModule.datetime(1,1,1,1,1,1)
            # self.startTime = startTime.combine(dateObject, self.startTime)
            # self.endTime = endTime.combine(dateObject, self.endTime)
            # self._promoteTimeFlag = True
    
    # def sorted_key(self,x):
        # return x.startTime
    
if __name__ == '__main__':
    test2 = CBlinksCaliLabels()
    test2.writeInfoForMatlab(r'.')