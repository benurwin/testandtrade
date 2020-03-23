# TODO:
# -do all technical indicators
# -add functionality to add extra columns to the dataframe if you want
# -add functionality to precompute some values
# -change saved dl fileName to be more specific to the data eg AAPL-Daily-2018-2019
# -make display() print() compatible
import sys
import pandas as pd
import numpy as np
import datetime as dt
import warnings
import pickle
import os
import pathos.multiprocessing as mp
import intrinio_sdk
from intrinio_sdk.rest import ApiException
import time
import datetime


  
class dataloader:
    # Checks some things:
    # -if the source of data is given and is supported
    # -if the instrument is given
    # Then calls the required functions to lod the data from the relevant sources
    def __init__(self, source, apiKey=None, dataType=None, instrument=None, fileName=None, verbose=1):
        if(type(source)!=str):
            raise ValueError("dataloader requires source input to be a string")
        elif(source!="local" and source!="alphavantage" and source!="preloaded"):
            raise ValueError("Invalid source for dataloader. Use local, alphavantage or preloaded instead.")
        elif(instrument==None):
            raise ValueError("dataloader requires an instrument.")
        elif(dataType==None):
            raise ValueError("dataloader requires a dataType.")
        elif(type(dataType)!=str):
            raise ValueError("dataloader requires dataType input to be a string")
        elif(type(instrument)!=str):
            raise ValueError("dataloader requires instrument input to be a string")
        self.__instrument = instrument
        self.__dataType = dataType
        self.__source = source
        self.__precomputed = []
        self.__verbose =  verbose
        self.fundamentals = None
        if(verbose>0):
            print("Data loading from " + source)
        if(source=='local'):
            self.__load_LOCAL(fileName)
        if(source=="alphavantage"):
            self.__load_ALPHAVANTAGE(apiKey, dataType, instrument)
        if(source=="preloaded"):
            self.__load()
# fvdbsnam,
    # Function role: Loads data from alphavantage api
    # Checks some things:
    # -Checks that an api key is given
    # -checks that a dataType is given
    # -checks that an instrument is given
    # Then it checks if the dataType is a correct one and converts it to a string that the alphavantage api understands
    # Then loads the data from the api
    # Then sorts it and stores it in self.data
    def __load_ALPHAVANTAGE(self, apiKey=None, dataType=None, instrument=None):
        if(apiKey==None):
            raise ValueError("dataloader requires an apiKey when using alphavantage.")
        elif(type(apiKey)!=str):
            raise ValueError("dataloader requires apiKey to be a string.")
        alphavantageDataType = None
        if(dataType=="intraday"):
            alphavantageDataType = "TIME_SERIES_INTRADAY"
        if(dataType=="daily"):
            alphavantageDataType = "TIME_SERIES_DAILY"
        if(dataType=="weekly"):
            alphavantageDataType = "TIME_SERIES_WEEKLY"
        if(dataType=="monthly"):
            alphavantageDataType = "TIME_SERIES_MONTHLY"
        if(alphavantageDataType==None):
            raise ValueError("Invalid dataType. Use intraday, daily, weekly or monthly.")
        data = pd.read_csv('https://www.alphavantage.co/query?function='+alphavantageDataType+'&outputsize=full&symbol='+instrument+'&interval=1min&apikey='+apiKey+'&datatype=csv')
        if(data.columns.any()=="{"):
            raise ValueError("Alphvantage has responded with an error: " + data["{"][0])
        data = data.rename(columns={"timestamp":"DATE","open":"OPEN","high":"HIGH","low":"LOW","close":"CLOSE","volume":"VOLUME"})
        warnings.filterwarnings('ignore', '.*.*',)
        for x in range(0,data.shape[0]):
            data["DATE"][x] = pd.to_datetime(data.iloc[x]["DATE"], format='%Y-%m-%d')

        for index in range(0,data.shape[0]-2):
            if(data["DATE"][index].day==data["DATE"][index+1].day):
                raise ValueError("The data comtains two sets of data for a single day")
        self.data = data

    #Function role: loads data from local Files
    # Checks some things:
    # -fileName is given
    # -file exists
    # Then loads the data into a dataframe and sorts it out while checking all relevant columns are given
    # Then stores the data in self.data
    def __load_LOCAL(self, fileName=None):
        if(fileName==None):
            raise ValueError("dataloader requires a fileName when loading a local file.")
        if(type(fileName)!=str):
            raise ValueError("fileName must be a string.")
        elif(os.path.exists(fileName)!=True):
            raise ValueError("dataloader requires a valid file in the directory.")
        elif(fileName[len(fileName)-1]!="v" or fileName[len(fileName)-2]!="s" or fileName[len(fileName)-3]!="c" or fileName[len(fileName)-4]!="."):
            raise ValueError("fileName must be a csv file in the directory.")
        else:
            data = pd.read_csv(fileName)
            newData = pd.DataFrame()
            found = -1
            lower = -1
            for x in range(0,data.columns.shape[0]):
                if(data.columns[x]=="Date" ):
                    found = x
                    break
                if(data.columns[x]=="date"):
                    found = x
                    lower = 1
                    break
            if(found==-1):
                raise ValueError("dataloader requires a Date column in localy loaded csv files.")
            if(lower == 1):
                newData['DATE'] = data['date']
            else:
                newData['DATE'] = data['Date']
            newData["DATE"] = self.__sortDate(newData["DATE"])

            found = -1
            lower = -1
            for x in range(0,data.columns.shape[0]):
                if(data.columns[x]=="Open"):
                    found=x
                    break
                if(data.columns[x]=="open"):
                    found = x
                    lower = 1
                    break
            if(found==-1):
                raise ValueError("dataloader requires a Open column in localy loaded csv files.")
            if(lower == 1):
                newData['OPEN'] = data['open']
            else:
                newData['OPEN'] = data['Open']

            found = -1
            lower = -1
            for x in range(0,data.columns.shape[0]):
                if(data.columns[x]=="High"):
                    found=x
                    break
                if(data.columns[x]=="high"):
                    found = x
                    lower = 1
                    break
            if(found==-1):
                raise ValueError("dataloader requires a High column in localy loaded csv files.")
            if(lower == 1):
                newData['HIGH'] = data['high']
            else:
                newData['HIGH'] = data['High']

            found = -1
            lower = -1
            for x in range(0,data.columns.shape[0]):
                if(data.columns[x]=="Low"):
                    found=x
                    break
                if(data.columns[x]=="low"):
                    found = x
                    lower = 1
                    break
            if(found==-1):
                raise ValueError("dataloader requires a Low column in localy loaded csv files.")
            if(lower == 1):
                newData['LOW'] = data['low']
            else:
                newData['LOW'] = data['Low']

            found = -1
            lower = -1
            for x in range(0,data.columns.shape[0]):
                if(data.columns[x]=="Close"):
                    found=x
                    break
                if(data.columns[x]=="close"):
                    found = x
                    lower = 1
                    break
            if(found==-1):
                raise ValueError("dataloader requires a Close column in localy loaded csv files.")
            if(lower == 1):
                newData['CLOSE'] = data['close']
            else:
                newData['CLOSE'] = data['Close']

            found = -1
            lower = -1
            for x in range(0,data.columns.shape[0]):
                if(data.columns[x]=="Volume"):
                    found=x
                    break
                if(data.columns[x]=="volume"):
                    found = x
                    lower = 1
                    break
            if(found==-1):
                raise ValueError("dataloader requires a Volume column in localy loaded csv files.")
            if(lower == 1):
                newData['VOLUME'] = data['volume']
            else:
                newData['VOLUME'] = data['Volume']
            newData = newData.sort_values(by='DATE',ascending=False)
            newData.index = range(newData.shape[0])
            self.data= newData
            for index in range(0,self.data.shape[0]-2):
                if(self.data["DATE"][index].day==self.data["DATE"][index+1].day):
                    raise ValueError("The data comtains two sets of data for a single day")

    # precomputes values and add the to the dataframe
    def precompute(self, indicator, days=None, type="OPEN", funct=None, slow=None, fast=None, multiCore = False, verbose=None):
        self.days = days
        self.type = type
        self.funct = funct
        self.slow = slow
        self.fast = fast
        if(self.days==None):
            self.days = "NONE"
        elif(not isinstance(self.days, int)):
            raise ValueError("days attribute must be an int for precompute")
        if(self.funct==None):
            self.funct = "NONE"
        elif(not isinstance(self.funct, str)):
            raise ValueError("funct attribute must be an str for precompute")
        if(self.slow==None):
            self.slow = "NONE"
        elif(not isinstance(self.slow, int)):
            raise ValueError("slow attribute must be an int for precompute")
        if(self.fast==None):
            self.fast = "NONE"
        elif(not isinstance(self.fast, int)):
            raise ValueError("fast attribute must be an int for precompute")
        if(not isinstance(indicator, str)):
            raise ValueError("indicator attribute must be an str for precompute")
        indicator = indicator
        if(verbose==None):
            verbose=self.__verbose
        if(verbose>0):
            print("precomputing values")
        if(multiCore==True):
            if((indicator + str(self.days) + self.type + self.funct + str(self.slow) + str(self.fast)).upper() in self.__precomputed):
                return

            from pathos.multiprocessing import ProcessingPool as Pool
            import multiprocessing
            pool = Pool()

            found = False

            if(indicator == "EMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute EMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_EMA, range(0,self.data.shape[0]))
                found = True

            if(indicator == "SMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute SMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_SMA, range(0,self.data.shape[0]))
                found = True

            if(indicator == "WMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute WMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_WMA, range(0,self.data.shape[0]))
                found = True

            if(indicator == "DEMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute DEMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_DEMA, range(0,self.data.shape[0]))
                found = True

            if(indicator == "TEMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute TEMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_TEMA, range(0,self.data.shape[0]))
                found = True

            if(indicator == "TRIMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute TRIMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_TRIMA, range(0,self.data.shape[0]))
                found = True

            if(indicator == "KAMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute KAMA requires a days attribute")
                if(self.fast=="NONE"):
                    raise ValueError("precompute KAMA requires a fast attribute")
                if(self.slow=="NONE"):
                    raise ValueError("precompute KAMA requires a slow attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()] = pool.map(self.__precomputeApply_TRIMA, range(0,self.data.shape[0]))
                found = True

            if(indicator == "VWAP"):
                if(self.days=="NONE"):
                    raise ValueError("precompute VWAP requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_VWAP, range(0,self.data.shape[0]))
                found = True

            if(indicator == "MACD"):
                self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_MACD, range(0,self.data.shape[0]))
                found = True

            if(indicator == "MACDEXT"):
                if(self.funct=="NONE"):
                    raise ValueError("precompute MACDEXT requires a funct attribute")
                if(self.slow=="NONE"):
                    raise ValueError("precompute MACDEXT requires a slow attribute")
                if(self.fast=="NONE"):
                    raise ValueError("precompute MACDEXT requires a fast attribute")
                self.data[(indicator + "NONE" + self.type + self.funct + str(self.slow) + str(self.fast)).upper()] = np.nan
                self.data[(indicator + "NONE" + self.type + self.funct + str(self.slow) + str(self.fast)).upper()] = pool.map(self.__precomputeApply_MACDEXT, range(0,self.data.shape[0]))
                found = True

            if(indicator == "STOCH"):
                self.data[(indicator + "NONE" + "NONE" + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + "NONE" + "NONE" + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_STOCH, range(0,self.data.shape[0]))
                found = True

            if(indicator == "RSI"):
                if(self.days=="NONE"):
                    raise ValueError("precompute RSI requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_RSI, range(0,self.data.shape[0]))
                found = True

            if(indicator == "STOCHRSI"):
                if(self.days=="NONE"):
                    raise ValueError("precompute STOCHRSI requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_STOCHRSI, range(0,self.data.shape[0]))
                found = True

            if(indicator == "WILLR"):
                if(self.days=="NONE"):
                    raise ValueError("precompute WILLR requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_WILLR, range(0,self.data.shape[0]))
                found = True

            if(indicator == "APO"):
                if(self.fast=="NONE"):
                    raise ValueError("precompute APO requires a fast attribute")
                if(self.slow=="NONE"):
                    raise ValueError("precompute APO requires a slow attribute")
                self.data[(indicator + "NONE" + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()] = np.nan
                self.data[(indicator + "NONE" + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()] = pool.map(self.__precomputeApply_APO, range(0,self.data.shape[0]))
                found = True

            if(indicator == "PPO"):
                self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_PPO, range(0,self.data.shape[0]))
                found = True

            if(indicator == "MOM"):
                if(self.days=="NONE"):
                    raise ValueError("precompute MOM requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_MOM, range(0,self.data.shape[0]))
                found = True

            if(indicator == "BOP"):
                if(self.days=="NONE"):
                    raise ValueError("precompute BOP requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_BOP, range(0,self.data.shape[0]))
                found = True

            if(indicator == "CCI"):
                if(self.days=="NONE"):
                    raise ValueError("precompute CCI requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_CCI, range(0,self.data.shape[0]))
                found = True

            if(indicator == "CMO"):
                if(self.days=="NONE"):
                    raise ValueError("precompute CMO requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_CMO, range(0,self.data.shape[0]))
                found = True

            if(indicator == "ROC"):
                if(self.days=="NONE"):
                    raise ValueError("precompute ROC requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = np.nan
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = pool.map(self.__precomputeApply_ROC, range(0,self.data.shape[0]))
                found = True

            if(found==False):
                raise ValueError( indicator + " is not a recognised indicator for use in precompute")

            self.__precomputed = self.get_PRECOMPUTED_INDICATORS()
        else:

            if((indicator + str(self.days) + self.type + self.funct + str(self.slow) + str(self.fast)).upper() in self.__precomputed):
                return
            found = False

            if(indicator == "EMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute EMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_EMA)
                found = True

            if(indicator == "SMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute SMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_SMA)
                found = True

            if(indicator == "WMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute WMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_WMA)
                found = True

            if(indicator == "DEMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute DEMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_DEMA)
                found = True

            if(indicator == "TEMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute TEMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_TEMA)
                found = True

            if(indicator == "TRIMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute TRIMA requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_TRIMA)
                found = True

            if(indicator == "KAMA"):
                if(self.days=="NONE"):
                    raise ValueError("precompute KAMA requires a days attribute")
                if(self.fast=="NONE"):
                    raise ValueError("precompute KAMA requires a fast attribute")
                if(self.slow=="NONE"):
                    raise ValueError("precompute KAMA requires a slow attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()].apply(self.__precomputeApply_TRIMA)
                found = True

            if(indicator == "VWAP"):
                if(self.days=="NONE"):
                    raise ValueError("precompute VWAP requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_VWAP)
                found = True

            if(indicator == "MACD"):
                self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_MACD)
                found = True

            if(indicator == "MACDEXT"):
                if(self.funct=="NONE"):
                    raise ValueError("precompute MACDEXT requires a funct attribute")
                if(self.slow=="NONE"):
                    raise ValueError("precompute MACDEXT requires a slow attribute")
                if(self.fast=="NONE"):
                    raise ValueError("precompute MACDEXT requires a fast attribute")
                self.data[(indicator + "NONE" + self.type + self.funct + str(self.slow) + str(self.fast)).upper()] = range(0,self.data.shape[0])
                self.data[(indicator + "NONE" + self.type + self.funct + str(self.slow) + str(self.fast)).upper()] = self.data[(indicator + "NONE" + self.type + self.funct + str(self.slow) + str(self.fast)).upper()].apply(self.__precomputeApply_MACDEXT)
                found = True

            if(indicator == "RSI"):
                if(self.days=="NONE"):
                    raise ValueError("precompute RSI requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_RSI)
                found = True

            if(indicator == "STOCHRSI"):
                if(self.days=="NONE"):
                    raise ValueError("precompute STOCHRSI requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_STOCHRSI)
                found = True

            if(indicator == "STOCH"):
                self.data[(indicator + "NONE" + "NONE" + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + "NONE" + "NONE" + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + "NONE" + "NONE" + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_STOCH)
                found = True

            if(indicator == "WILLR"):
                if(self.days=="NONE"):
                    raise ValueError("precompute WILLR requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_WILLR)
                found = True

            if(indicator == "APO"):
                if(self.fast=="NONE"):
                    raise ValueError("precompute APO requires a fast attribute")
                if(self.slow=="NONE"):
                    raise ValueError("precompute APO requires a slow attribute")
                self.data[(indicator + "NONE" + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()] = range(0,self.data.shape[0])
                self.data[(indicator + "NONE" + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()] = self.data[(indicator + "NONE" + self.type + "NONE" + str(self.slow) + str(self.fast)).upper()].apply(self.__precomputeApply_APO)
                found = True

            if(indicator == "PPO"):
                self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + "NONE" + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_PPO)
                found = True

            if(indicator == "MOM"):
                if(self.days=="NONE"):
                    raise ValueError("precompute MOM requires a days attribute")
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + self.type + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_MOM)
                found = True

            if(indicator == "BOP"):
                if(self.days=="NONE"):
                    raise ValueError("precompute BOP requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_BOP)
                found = True

            if(indicator == "CCI"):
                if(self.days=="NONE"):
                    raise ValueError("precompute CCI requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_CCI)
                found = True

            if(indicator == "CMO"):
                if(self.days=="NONE"):
                    raise ValueError("precompute CMO requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_CMO)
                found = True

            if(indicator == "ROC"):
                if(self.days=="NONE"):
                    raise ValueError("precompute ROC requires a days attribute")
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = range(0,self.data.shape[0])
                self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()] = self.data[(indicator + str(self.days) + "NONE" + "NONE" + "NONE" + "NONE").upper()].apply(self.__precomputeApply_ROC)
                found = True

            if(found==False):
                raise ValueError( indicator + " is not a recognised indicator for use in precompute")


            self.__precomputed = self.get_PRECOMPUTED_INDICATORS()
        if(verbose>0):
            print("Finished precomputing")

        delattr(self, "days")
        delattr(self, "type")
        delattr(self, "funct")
        delattr(self, "slow")
        delattr(self, "fast")

    # The following functions are helper functions to precompute
    def __precomputeApply_EMA(self, row):
        return self.get_EMA(row, self.days, self.type, 2)

    def __precomputeApply_SMA(self, row):
        return self.get_SMA(row, self.days, self.type)

    def __precomputeApply_WMA(self, row):
        return self.get_WMA(row, self.days, self.type)

    def __precomputeApply_DEMA(self, row):
        return self.get_DEMA(row, self.days, self.type)

    def __precomputeApply_TEMA(self, row):
        return self.get_TEMA(row, self.days, self.type)

    def __precomputeApply_TRIMA(self, row):
        return self.get_TRIMA(row, self.days, self.type)

    def __precomputeApply_KAMA(self, row):
        return self.get_KAMA(row, self.days, self.type,  self.fast, self.slow)

    def __precomputeApply_VWAP(self, row):
        return self.get_VWAP(row, self.days, self.type)

    def __precomputeApply_MACD(self, row):
        return self.get_MACD(row, self.type)

    def __precomputeApply_MACDEXT(self, row):
        return self.get_MACDEXT(row, self.type, self.funct, self.slow, self.fast)

    def __precomputeApply_STOCH(self, row):
        return self.get_STOCH(row)

    def __precomputeApply_RSI(self, row):
        return self.get_RSI(row, self.days, self.type)

    def __precomputeApply_STOCHRSI(self, row):
        return self.get_STOCHRSI(row, self.days, self.type)

    def __precomputeApply_WILLR(self, row):
        return self.get_WILLR(row, self.days)

    def __precomputeApply_APO(self, row):
        return self.get_APO(row, self.fast, self.slow, self.type)

    def __precomputeApply_PPO(self, row):
        return self.get_PPO(row, self.type)

    def __precomputeApply_MOM(self, row):
        return self.get_MOM(row, self.days, self.type)

    def __precomputeApply_BOP(self, row):
        return self.get_BOP(row, self.days)

    def __precomputeApply_CCI(self, row):
        return self.get_CCI(row, self.days)

    def __precomputeApply_CMO(self, row):
        return self.get_CMO(row, self.days)

    def __precomputeApply_ROC(self, row):
        return self.get_ROC(row, self.days)

    # Returns a list of precomputed values for the dataloader
    def get_PRECOMPUTED_INDICATORS(self, verbose=None):
        if(verbose==None):
            verbose=self.__verbose
        out = []
        for col in self.data.columns:
            if(col!="HIGH" and col!="LOW" and col!="OPEN" and col!="CLOSE" and col!="VOLUME" and col!="DATE"):
                out.append(col)
        if(verbose>0):
            print(out)
        return out

    # Function role: Helper function for __load_LOCAL  (Sorts the dates into the required format using one conversion to avoid confusion of pd.to_datetime())
    def __sortDate(self,newDates1):
        warnings.filterwarnings('ignore', '.*.*',)
        holder = newDates1
        newDates = newDates1
        try:
            for x in range(0,newDates1.shape[0]):
                newDates.loc[x] = pd.to_datetime(newDates.iloc[x], format='%Y-%m-%d')
        except ValueError:
            try:
                newDates = holder
                for x in range(0,newDates1.shape[0]):
                    newDates.loc[x] = pd.to_datetime(newDates.iloc[x], format='%Y-%d-%m')
                return
            except ValueError:
                try:
                    newDates = holder
                    for x in range(0,newDates1.shape[0]):
                        newDates.loc[x] = pd.to_datetime(newDates.iloc[x], format='%d-%m-%Y')
                except ValueError:
                    try:
                        newDates = holder
                        for x in range(0,newDates1.shape[0]):
                            newDates.loc[x] = pd.to_datetime(newDates.iloc[x], format='%m-%d-%Y')
                    except ValueError:
                        try:
                            for x in range(0,newDates1.shape[0]):
                                newDates.loc[x] = pd.to_datetime(newDates.iloc[x], format='%Y/%m/%d')
                        except ValueError:
                            try:
                                newDates = holder
                                for x in range(0,newDates1.shape[0]):
                                    newDates.loc[x] = pd.to_datetime(newDates.iloc[x], format='%Y/%d/%m')
                                return
                            except ValueError:
                                try:
                                    newDates = holder
                                    for x in range(0,newDates1.shape[0]):
                                        newDates.loc[x] = pd.to_datetime(newDates.iloc[x], format='%d/%m/%Y')
                                except ValueError:
                                    try:
                                        newDates = holder
                                        for x in range(0,newDates1.shape[0]):
                                            newDates.loc[x] = pd.to_datetime(newDates.iloc[x], format='%m/%d/%Y')
                                    except ValueError:
                                        raise ValueError("Inputs for the date column are not of supported format try '%Y-%m-%d' format.")

        return newDates

    def addFundamentals(self, source, fileName=None, apiKey=None, removeColumnsWithNan=False, setNansToZero=False, verbose=None):
        if(verbose==None):
            verbose = self.__verbose
        if(verbose>0):
            print("Loading fundamentals from " + source)

        if(source.upper()!="INTRINO" and source.upper()!="LOCAL"):
            raise ValueError("addFundamentals takes only INTRINO or LOCAL for its source attribute.")
        if(source.upper()=="LOCAL"):
            if(fileName==None):
                raise ValueError("addFundamentals requires a fileName when loading local.")
            self.addLocalFundamentals(fileName, verbose)
        if(source.upper()=="INTRINO"):
            if(apiKey==None):
                raise ValueError("addFundamentals requires a apiKey when loading from intrino.")
            self.addIntrinoFundamentals(apiKey, verbose)
        if(removeColumnsWithNan==True):
            list = []
            for col in self.fundamentals.columns:
                if(col!="DATE" and self.fundamentals[col].isna().any()):
                    list.append(col)
            self.fundamentals = self.fundamentals.drop(columns=list)
        if(setNansToZero==True):
            for col in self.fundamentals.columns:
                if(col!="DATE" and self.fundamentals[col].isna().any()):
                    for x in range(0,self.fundamentals.shape[0]):
                        if(np.isnan(self.fundamentals[col][x])):
                            self.fundamentals.at[x,col] = 0


    def addLocalFundamentals(self, fileName, verbose):
        if(os.path.exists(fileName)!=True):
            raise ValueError(fileName + " is not a valid file in the directory.")
        if(fileName[len(fileName)-1]!="v" or fileName[len(fileName)-2]!="s" or fileName[len(fileName)-3]!="c" or fileName[len(fileName)-4]!="."):
            raise ValueError(fileName + " must be a csv file in the directory.")
        data = pd.read_csv(fileName)
        if("DATE" not in data.columns):
            raise ValueError("DATE column is needed.")
        self.__sortDate(data["DATE"])
        data.sort_values('DATE',ascending=False)
        data.index = range(data.shape[0])
        self.fundamentals = data

    def addIntrinoFundamentals(self, apiKey, verbose):
        def findDate(df, date):
            for x in range(df.shape[0]):
                if(df["DATE"][x].month==date.month and df["DATE"][x].year==date.year):
                    return x
            df.at[df.shape[0], "DATE"] = date
            return df.shape[0] - 1

        intrinio_sdk.ApiClient().configuration.api_key['api_key'] = apiKey
        fundamentals_api = intrinio_sdk.FundamentalsApi()
        first = 1
        df = 0
        now = datetime.datetime.now()
        for x in range(2010,now.year):
            for y in range(1,5):
                for z in ["-calculations-","-income_statement-","-cash_flow_statement-"]:
                    id = self.__instrument + z + str(x) + '-Q' + str(y)# str | The Intrinio ID or lookup code (ticker-statement-year-period) for the Fundamental
                    if(verbose>1):
                        print(id)
                    go=True
                    while (go == True):
                        try:
                            api_response = fundamentals_api.get_fundamental_standardized_financials(id)
                            if(first == 1):
                                first = 0
                                df = pd.DataFrame([0], columns=["DATE"])
                                df.at[0,"DATE"] = pd.to_datetime(api_response.fundamental.end_date, format='%Y/%m/%d')
                                for i in range(0,len(api_response.standardized_financials)):
                                    df[api_response.standardized_financials[i].data_tag.tag] = np.nan
                                    df.at[0, api_response.standardized_financials[i].data_tag.tag] = api_response.standardized_financials[i].value
                            else:
                                index = findDate(df, pd.to_datetime(api_response.fundamental.end_date, format='%Y/%m/%d'))
                                for i in range(0,len(api_response.standardized_financials)):
                                    df.at[index, api_response.standardized_financials[i].data_tag.tag] = api_response.standardized_financials[i].value
                            go=False
                        except ApiException as e:
                            if(e.status==401):
                                if(verbose>0):
                                    print("Intrino response: Unauthorized – Your User/Password API Keys are incorrect.")
                                go=False
                                return
                            if(e.status==403):
                                if(verbose>0):
                                    print("Intrino response: Forbidden – You are not subscribed to the data feed requested.")
                                go=False
                                return
                            if(e.status==404):
                                if(verbose>0):
                                    print("Intrino response: Not Found – The endpoint requested does not exist.")
                                go=False
                            if(e.status==429):
                                if(verbose>0):
                                    print("Intrino response: Too Many Requests – You have hit a limit.")
                                    print("Sleeping for 20 seconds")
                                time.sleep(20)
                            if(e.status==500):
                                if(verbose>0):
                                    print("Intrino response: Internal Server Error – We had a problem with our server. Try again later.")
                                    print("Sleeping for 20 seconds")
                                time.sleep(20)
                            if(e.status==503):
                                if(verbose>0):
                                    print("Intrino response: Service Unavailable – You have hit your throttle limit or Intrinio may be experiencing high system load.")
                                    print("Sleeping for 20 seconds")
                                time.sleep(20)

        df["DATE"] = self.__sortDate(df["DATE"])
        df = df.iloc[::-1]
        df.index = range(df.shape[0])
        self.fundamentals = df

    # Function role: cleans the data with option to remove zero values and very low values
    def clean(self, nans=True, zerosAndLows=0, verbose=None):
        if(verbose==None):
            verbose=self.__verbose
        if(verbose>0):
            print("Cleaning data ...")
        cols = self.data.columns
        for y in range(0,self.data.shape[1]):
            for b in range(0,self.data.shape[0]):
                x = self.data.shape[0] - (b + 1)
                if(nans==True and cols[y]!="DATE" and cols[y]!="VOLUME"and cols[y] not in self.__precomputed):
                    self.data.at[x, cols[y]] = self.__sortNan(cols[y], x, -1)
                if(zerosAndLows!=0 and cols[y]!="DATE" and cols[y]!="VOLUME"and cols[y] not in self.__precomputed and x<self.data.shape[0]-2):
                    self.data.at[x, cols[y]] = self.__sortZeros(cols[y], x, 1, zerosAndLows)
                elif(zerosAndLows!=0 and cols[y]!="DATE" and cols[y]!="VOLUME"and cols[y] not in self.__precomputed and x<self.data.shape[0]-1):
                    self.data.at[x, cols[y]] = self.__sortZeros(cols[y], x, -1, zerosAndLows)
        for y in range(1,self.data.shape[1]-1):
            if(self.data[cols[y]][self.data.shape[0]-1]==0 and cols[y]!="Date" and cols[y]!="Volume" and cols[y] not in self.__precomputed):
                self.data[cols[y]][self.data.shape[0]-1] = self.data[cols[y]][self.data.shape[0]-2]
        if(verbose>0):
            print("Data cleaned")

    # Function role: Helper function for clean()
    def __sortNan(self, colName, index, upOrDown):
        if(np.isnan(self.data[colName][index])):
            if(index<self.data.shape[0]-1 and index>0):
                return self.__sortNan(colName, index+upOrDown, upOrDown)
            else:
                if(index>self.data.shape[0]-2):
                    return self.__sortNan(colName, index-1, -1)
                if(index<1):
                    return self.__sortNan(colName, index+1, +1)
        else:
            return self.data[colName][index]

    # Function role: Helper function for clean()
    def __sortZeros(self, colName, index, upOrDown, zerosAndLows):
        if(self.data[colName][index]==0 or self.data[colName][index]<self.data[colName][index+1]/zerosAndLows):
            if(index<=self.data.shape[0]-1 and index>=0):
                return self.__sortZeros(colName, index+upOrDown, upOrDown, zerosAndLows)
            else:
                if(index>self.data.shape[0]-2):
                    return self.__sortZeros(colName, index-1, -1, zerosAndLows)
                if(index<1):
                    return self.__sortZeros(colName, index+1, +1, zerosAndLows)
        else:
            return self.data[colName][index]

    # Function role: Displays the data in the dataloader
    def display(self):
        print("Core data: ")
        print(self.data)
        print("Fundamentals: ")
        print(self.fundamentals)

    # Function role: Saves a copy of the data in the dataloader in "./dataloaders"
    def save(self, verbose=None):
        if(verbose==None):
            verbose=self.__verbose
        try:
            # Create target Directory
            os.mkdir("dataloaders")
            file = open("./dataloaders/" + str(self.__instrument) + "-dataloader.pkl", 'wb')
            pickle.dump([self.data,self.fundamentals], file)
            file.close()
        except FileExistsError:
            file = open("./dataloaders/" + str(self.__instrument) + "-dataloader.pkl", 'wb')
            pickle.dump([self.data,self.fundamentals], file)
            file.close()
        if(verbose>0):
            print(self.__instrument+" "+self.__dataType+" from "+self.__source+" dataloader saved")

    # Function role: Called by __intit__() and loads the data saved with instrument name that was provided
    def __load(self):
        if(os.path.exists("./dataloaders/" + str(self.__instrument) + "-dataloader.pkl")==False):
            raise ValueError("preloaded requires saved data for this instument and none was found.")
        file = open("./dataloaders/" + str(self.__instrument) + "-dataloader.pkl", 'rb')
        data = pickle.load(file)
        file.close()
        self.data = data[0]
        self.fundamentals  = data[1]

        for col in self.data:
            if(col != "DATE" and col != "OPEN" and col != "HIGH" and col != "LOW" and col != "CLOSE" and col != "VOLUME"):
                self.__precomputed.append(col)

    # Function role: returns the data in the dataloader
    def output(self):
        return self.data

    # Function role: returns the info in the dataloader
    def info(self, verbose=None):
        if(verbose==None):
            verbose=self.__verbose
        if(verbose>0):
            print(self.__instrument, self.__dataType, self.__source)
        return  self.__instrument, self.__dataType, self.__source

# (indicator + days + type + funct + str(slow) + str(fast)).upper()
# The following functions compute different technical indicators for the data
    def get_SMA(self, index, days, type):
        if(self.__precomputed!=[]):
            if("SMA" + str(days) + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["SMA" + str(days) + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["SMA" + str(days) + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+days>self.data.shape[0] or days<1):
                    return None
                else:
                    return self.data[type][index:index+days].mean()
        else:
            if(index+days>self.data.shape[0] or days<1):
                return None
            else:
                return self.data[type][index:index+days].mean()

    def get_EMA(self, index, days, type, smoothing):
        if(self.__precomputed!=[]):
            if("EMA" + str(days) + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["EMA" + str(days) + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["EMA" + str(days) + type + "NONE" + "NONE" + "NONE" ][index]
            else:
                if(index+days>self.data.shape[0] or days<1):
                    return None
                else:
                    sum = 0
                    x=index+days-1
                    sum = self.data[type][x]
                    while x>index-1 and x>=0:
                        sum = (self.data[type][x]-sum)*(smoothing/(days+1)) + sum
                        x = x - 1
                    return sum
        else:
            if(index+days>self.data.shape[0] or days<1):
                return None
            else:
                sum = 0
                x=index+days-1
                sum = self.data[type][x]
                while x>index-1 and x>=0:
                    sum = (self.data[type][x]-sum)*(smoothing/(days+1)) + sum
                    x = x - 1
                return sum

    def get_WMA(self, index, days, type):
        if(self.__precomputed!=[]):
            if("WMA" + str(days) + type + "NONE" + "NONE" + "NONE"  in self.__precomputed):
                if(np.isnan(self.data["WMA" + str(days) + type + "NONE" + "NONE" + "NONE" ][index])):
                    return None
                else:
                    return self.data["WMA" + str(days) + type + "NONE" + "NONE" + "NONE" ][index]
            else:
                if(index+days>self.data.shape[0] or days<1):
                    return None
                else:
                    sum = 0
                    xsum = 0
                    data=self.output()[index:index+days]
                    for x in range(index,index+days):
                        sum = sum + data[type][x]*(days+index-x)
                        xsum = xsum + (x - index + 1)
                    sum = sum/xsum
                    return sum
        else:
            if(index+days>self.data.shape[0] or days<1):
                return None
            else:
                sum = 0
                xsum = 0
                data=self.output()[index:index+days]
                for x in range(index,index+days):
                    sum = sum + data[type][x]*(days+index-x)
                    xsum = xsum + (x - index + 1)
                sum = sum/xsum
                return sum

    def get_DEMA(self, index, days, type):
        if(self.__precomputed!=[]):
            if("DEMA" + str(days) + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["DEMA" + str(days) + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["DEMA" + str(days) + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+2*days-1>self.data.shape[0] or days<1):
                    return None
                else:
                    emas = np.zeros(days)
                    for x in range(0,days):
                        emas[x] = self.get_EMA(index+x,days,type,2)
                    sum = 0
                    sum = emas.sum()/days
                    x=days-2
                    while(x>=0):
                        sum = (emas[x]-sum)*(2/(days+1)) + sum
                        x = x - 1
                    emaEma =  sum
                    return 2*emas[0] - emaEma
        else:
            if(index+2*days-1>self.data.shape[0] or days<1):
                return None
            else:
                emas = np.zeros(days)
                for x in range(0,days):
                    emas[x] = self.get_EMA(index+x,days,type,2)
                sum = 0
                sum = emas.sum()/days
                x=days-2
                while(x>=0):
                    sum = (emas[x]-sum)*(2/(days+1)) + sum
                    x = x - 1
                emaEma =  sum
                return 2*emas[0] - emaEma

    def get_TEMA(self, index, days, type):
        if(self.__precomputed!=[]):
            if("TEMA" + str(days) + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["TEMA" + str(days) + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["TEMA" + str(days) + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+3*days-1>self.data.shape[0] or days<1):
                    return None
                else:
                    ema1 = self.get_EMA(index, days, type, 2)
                    ema2s = np.zeros(days)
                    for x in range(0,days):
                        ema2s[x] = -1*(self.get_DEMA(index+x, days, type) - 2*self.get_EMA(index+x, days, type, 2))
                    sum = ema2s.sum()/days
                    x=days-2
                    while(x>=0):
                        sum = (ema2s[x]-sum)*(2/(days+1)) + sum
                        x = x - 1
                    ema3 =  sum
                    return 3*ema1 - 3*ema2s[0] + ema3
        else:
            if(index+3*days-1>self.data.shape[0] or days<1):
                return None
            else:
                ema1 = self.get_EMA(index, days, type, 2)
                ema2s = np.zeros(days)
                for x in range(0,days):
                    ema2s[x] = -1*(self.get_DEMA(index+x, days, type) - 2*self.get_EMA(index+x, days, type, 2))
                sum = ema2s.sum()/days
                x=days-2
                while(x>=0):
                    sum = (ema2s[x]-sum)*(2/(days+1)) + sum
                    x = x - 1
                ema3 =  sum
                return 3*ema1 - 3*ema2s[0] + ema3

    def get_TRIMA(self, index, days, type):
        if(self.__precomputed!=[]):
            if("TRIMA" + str(days) + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["TRIMA" + str(days) + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["TRIMA" + str(days) + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+2*days-1>self.data.shape[0] or days<1):
                    return None
                else:
                    sum = 0
                    for x in range(0,days):
                        sum = sum + self.get_SMA(index + x,days,type)
                    return sum/days
        else:
            if(index+2*days-1>self.data.shape[0] or days<1):
                return None
            else:
                sum = 0
                for x in range(0,days):
                    sum = sum + self.get_SMA(index + x,days,type)
                return sum/days

    def get_KAMA(self, index, days, type, fast, slow):
        if(self.__precomputed!=[]):
            if("KAMA-"+str(days)+"-"+type+"-"+str(fast)+"-"+str(slow) in self.__precomputed):
                if(np.isnan(self.data["KAMA-"+str(days)+"-"+type+"-"+str(fast)+"-"+str(slow)][index])):
                    return None
                else:
                    return self.data["KAMA-"+str(days)+"-"+type+"-"+str(fast)+"-"+str(slow)][index]
            else:
                if(days+11+index>=self.data.shape[0] or days<1):
                    return None
                else:
                    y = days - 1
                    kama = self.data[type][index+days]
                    while(y>=0):
                        sum = 0
                        for x in range(y,10+y):
                            sum = sum + abs(self.data[type][index+x] - self.data[type][index+x+1])
                        er =abs(self.data[type][index+y] - self.data[type][index+10+y])/sum
                        sc = (er *( (2/(fast+1)) - (2/(slow+1)) ) + (2/(slow+1)))**2
                        kama = kama + sc*(self.data[type][index+y] - kama)
                        y = y-1
                    return kama
        else:
            if(days+11+index>=self.data.shape[0] or days<1):
                return None
            else:
                y = days
                kama = self.data[type][index+y]
                while(y>=0):
                    sum = 0
                    for x in range(y,10+y):
                        sum = sum + abs(self.data[type][index+x] - self.data[type][index+x+1])
                    er =abs(self.data[type][index+y] - self.data[type][index+10+y])/sum
                    sc = (er *( (2/(fast+1)) - (2/(slow+1)) ) + (2/(slow+1)))**2
                    kama = kama + sc*(self.data[type][index+y] - kama)
                    y = y-1
                return kama

    # # # TODO: implement this
    # def get_MAMA(self, index, type):
    #     this = todo

    def get_VWAP(self, index, days, type):
        if(self.__precomputed!=[]):
            if("VWAP" + str(days) + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["VWAP" + str(days) + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["VWAP" + str(days) + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+days>self.data.shape[0] or days<1):
                    return None
                else:
                    sumPriTVol = 0
                    sumVol = 0
                    for x in range(0,days):
                        sumPriTVol = sumPriTVol + self.data[type][index+x]*self.data["VOLUME"][index+x]
                        sumVol = sumVol + self.data["VOLUME"][index+x]
                    return sumPriTVol/sumVol
        else:
            if(index+days>self.data.shape[0] or days<1):
                return None
            else:
                sumPriTVol = 0
                sumVol = 0
                for x in range(0,days):
                    sumPriTVol = sumPriTVol + self.data[type][index+x]*self.data["VOLUME"][index+x]
                    sumVol = sumVol + self.data["VOLUME"][index+x]
                return sumPriTVol/sumVol

    def get_MACD(self, index, type):
        if(self.__precomputed!=[]):
            if("MACD" + "NONE" + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["MACD" + "NONE" + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["MACD" + "NONE" + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+26>self.data.shape[0]):
                    return None
                else:
                    return self.get_EMA(index, 12, type, 2) - self.get_EMA(index, 26, type, 2)
        else:
            if(index+26>self.data.shape[0]):
                return None
            else:
                return self.get_EMA(index, 12, type, 2) - self.get_EMA(index, 26, type, 2)

    def get_MACDEXT(self, index, type, funct, slow, fast):
        if(self.__precomputed!=[]):
            if("MACDEXT" + "NONE" + type + funct + str(slow) + str(fast) in self.__precomputed):
                if(np.isnan(self.data["MACDEXT" + "NONE" + type + funct + str(slow) + str(fast)][index])):
                    return None
                else:
                    return self.data["MACDEXT" + "NONE" + type + funct + str(slow) + str(fast)][index]
            else:
                if(index+slow>self.data.shape[0] or slow<fast):
                    return None
                else:
                    if(funct=="EMA"):
                        return self.get_EMA(index, fast, type, 2) - self.get_EMA(index, slow, type, 2)
                    elif(funct=="SMA"):
                        return self.get_SMA(index, fast, type) - self.get_SMA(index, slow, type)
                    elif(funct=="DEMA"):
                        if(index+slow*2-1>self.data.shape[0]):
                            return None
                        else:
                            return self.get_DEMA(index, fast, type) - self.get_DEMA(index, slow, type)
                    elif(funct=="WMA"):
                        return self.get_WMA(index, fast, type) - self.get_WMA(index, slow, type)
                    elif(funct=="VWAP"):
                        return self.get_VWAP(index, fast, type) - self.get_VWAP(index, slow, type)
                    elif(funct=="TRIMA"):
                        if(index+slow*2-1>self.data.shape[0]):
                            return None
                        else:
                            return self.get_TRIMA(index, fast, type) - self.get_TRIMA(index, slow, type)
                    else:
                        raise ValueError("Check funct is a valid string: EMA, SMA, DEMA, WMA, WVAP or TRIMA.")
        else:
            if(index+slow>self.data.shape[0] or slow<fast):
                return None
            else:
                if(funct=="EMA"):
                    return self.get_EMA(index, fast, type, 2) - self.get_EMA(index, slow, type, 2)
                elif(funct=="SMA"):
                    return self.get_SMA(index, fast, type) - self.get_SMA(index, slow, type)
                elif(funct=="DEMA"):
                    if(index+slow*2-1>self.data.shape[0]):
                        return None
                    else:
                        return self.get_DEMA(index, fast, type) - self.get_DEMA(index, slow, type)
                elif(funct=="WMA"):
                    return self.get_WMA(index, fast, type) - self.get_WMA(index, slow, type)
                elif(funct=="VWAP"):
                    return self.get_VWAP(index, fast, type) - self.get_VWAP(index, slow, type)
                elif(funct=="TRIMA"):
                    if(index+slow*2-1>self.data.shape[0]):
                        return None
                    else:
                        return self.get_TRIMA(index, fast, type) - self.get_TRIMA(index, slow, type)
                else:
                    raise ValueError("Check funct is a valid string: EMA, SMA, DEMA, WMA, WVAP or TRIMA.")

    def get_STOCH(self, index):
        if(self.__precomputed!=[]):
            if("STOCH" + "NONE" + "NONE" + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(not isinstance(self.data["STOCH" + "NONE" + "NONE" + "NONE" + "NONE" + "NONE"][index], tuple)):
                    return None
                else:
                    return self.data["STOCH" + "NONE" + "NONE" + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+17>self.data.shape[0]):
                    return None
                else:
                    high = 0
                    low = 999999999999
                    for x in range(0,14):
                        if(self.data["HIGH"][index+x]>high):
                            high = self.data["HIGH"][index+x]
                        if(self.data["LOW"][index+x]<low):
                            low = self.data["LOW"][index+x]
                    perK = 100*(self.data["CLOSE"][index]-low)/(high-low)
                    k1 = perK
                    high = 0
                    low = 999999999999
                    for x in range(0,14):
                        if(self.data["HIGH"][index+1+x]>high):
                            high = self.data["HIGH"][index+1+x]
                        if(self.data["LOW"][index+1+x]<low):
                            low = self.data["LOW"][index+1+x]
                    k2 = 100*(self.data["CLOSE"][index+1]-low)/(high-low)
                    high = 0
                    low = 999999999999
                    for x in range(0,14):
                        if(self.data["HIGH"][index+2+x]>high):
                            high = self.data["HIGH"][index+2+x]
                        if(self.data["LOW"][index+2+x]<low):
                            low = self.data["LOW"][index+2+x]
                    k3 = 100*(self.data["CLOSE"][index+2]-low)/(high-low)
                    perD = (k1+k2+k3)/3
                    return (perK, perD)
        else:
            if(index+17>self.data.shape[0]):
                return None
            else:
                high = 0
                low = 999999999999
                for x in range(0,14):
                    if(self.data["HIGH"][index+x]>high):
                        high = self.data["HIGH"][index+x]
                    if(self.data["LOW"][index+x]<low):
                        low = self.data["LOW"][index+x]
                perK = 100*(self.data["CLOSE"][index]-low)/(high-low)
                k1 = perK
                high = 0
                low = 999999999999
                for x in range(0,14):
                    if(self.data["HIGH"][index+1+x]>high):
                        high = self.data["HIGH"][index+1+x]
                    if(self.data["LOW"][index+1+x]<low):
                        low = self.data["LOW"][index+1+x]
                k2 = 100*(self.data["CLOSE"][index+1]-low)/(high-low)
                high = 0
                low = 999999999999
                for x in range(0,14):
                    if(self.data["HIGH"][index+2+x]>high):
                        high = self.data["HIGH"][index+2+x]
                    if(self.data["LOW"][index+2+x]<low):
                        low = self.data["LOW"][index+2+x]
                k3 = 100*(self.data["CLOSE"][index+2]-low)/(high-low)
                perD = (k1+k2+k3)/3
                return (perK, perD)

    def get_RSI(self, index, days, type):
        if(self.__precomputed!=[]):
            if("RSI" + str(days) + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["RSI" + str(days) + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["RSI" + str(days) + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+days>=self.data.shape[0] or days<1):
                    return None
                else:
                    up = 0
                    down = 0
                    for x in range(index, index+days):
                        if(self.data[type][x]>self.data[type][x+1]):
                            up = up + (self.data[type][x]-self.data[type][x+1])
                        else:
                            down = down + (self.data[type][x+1]-self.data[type][x])
                    if(down==0):
                        return 100
                    up = up/days
                    down = down/days
                    return( 100-(100/( 1 + (up/down))))
        else:
            if(index+days>=self.data.shape[0] or days<1):
                return None
            else:
                up = 0
                down = 0
                for x in range(index, index+days):
                    if(self.data[type][x]>self.data[type][x+1]):
                        up = up + (self.data[type][x]-self.data[type][x+1])
                    else:
                        down = down + (self.data[type][x+1]-self.data[type][x])
                if(down==0):
                    return 100
                up = up/days
                down = down/days
                return( 100-(100/( 1 + (up/down))))

    def get_STOCHRSI(self, index, days, type):
        if(self.__precomputed!=[]):
            if("STOCHRSI" + str(days) + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["STOCHRSI" + str(days) + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["STOCHRSI" + str(days) + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+2*days>self.data.shape[0] or days<1):
                    return None
                else:
                    high = 0
                    low = 9999999
                    for x in range(0,days):
                        rsi = self.get_RSI(index+x, days, type)
                        if(rsi>high):
                            high = rsi
                        if(rsi<low):
                            low = rsi
                    if(self.get_RSI(index, days, type)==0):
                        return 0
                    elif(high==low ):
                        return 100
                    else:
                        return 100*(self.get_RSI(index,days,type)-low)/(high-low)
        else:
            if(index+2*days>self.data.shape[0] or days<1):
                return None
            else:
                high = 0
                low = 9999999
                for x in range(0,days):
                    rsi = self.get_RSI(index+x, days, type)
                    if(rsi>high):
                        high = rsi
                    if(rsi<low):
                        low = rsi
                if(self.get_RSI(index, days, type)==0):
                    return 0
                elif(high==low ):
                    return 100
                else:
                    return 100*(self.get_RSI(index,days,type)-low)/(high-low)

    def get_WILLR(self, index, days):
        if(self.__precomputed!=[]):
            if("WILLR" + str(days) + "NONE" + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["WILLR" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["WILLR" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+days>self.data.shape[0] or days<1):
                    return None
                else:
                    high = 0
                    low = 999999999999
                    for x in range(0,days):
                        if(self.data["HIGH"][index+x]>high):
                            high = self.data["HIGH"][index+x]
                        if(self.data["LOW"][index+x]<low):
                            low = self.data["LOW"][index+x]
                    return 100*(self.data["CLOSE"][index]-high)/(high-low)
        else:
            if(index+days>self.data.shape[0] or days<1):
                return None
            else:
                high = 0
                low = 999999999999
                for x in range(0,days):
                    if(self.data["HIGH"][index+x]>high):
                        high = self.data["HIGH"][index+x]
                    if(self.data["LOW"][index+x]<low):
                        low = self.data["LOW"][index+x]
                return 100*(self.data["CLOSE"][index]-high)/(high-low)

# # # TODO: implement this
#     def get_ADX(self, index, days):

#
# # # TODO: implement this
#     def get_ADXR(self, index, fast, slow):
#         this = todo

    def get_APO(self, index, fast, slow, type):
        if(self.__precomputed!=[]):
            if("APO" + "NONE" + type + "NONE" + str(slow) + str(fast) in self.__precomputed):
                if(np.isnan(self.data["APO" + "NONE" + type + "NONE" + str(slow) + str(fast)][index])):
                    return None
                else:
                    return self.data["APO" + "NONE" + type + "NONE" + str(slow) + str(fast)][index]
            else:
                if(index+slow>self.data.shape[0] or fast<1 or slow<1):
                    return None
                else:
                    return self.get_EMA(index,fast,type,2)-self.get_EMA(index,slow,type,2)
        else:
            if(index+slow>self.data.shape[0] or fast<1 or slow<1):
                return None
            else:
                return self.get_EMA(index,fast,type,2)-self.get_EMA(index,slow,type,2)

    def get_PPO(self, index, type):
        if(self.__precomputed!=[]):
            if("PPO" + "NONE" + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["PPO" + "NONE" + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["PPO" + "NONE" + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+26>self.data.shape[0]):
                    return None
                else:
                    return 100*(self.get_EMA(index,12,type,2)-self.get_EMA(index,26,type,2))/self.get_EMA(index,26,type,2)
        else:
            if(index+26>self.data.shape[0]):
                return None
            else:
                return 100*(self.get_EMA(index,12,type,2)-self.get_EMA(index,26,type,2))/self.get_EMA(index,26,type,2)

    def get_MOM(self, index, days, type):
        if(self.__precomputed!=[]):
            if("MOM" + str(days) + type + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["MOM" + str(days) + type + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["MOM" + str(days) + type + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+days>=self.data.shape[0] or days<1):
                    return None
                else:
                    return self.data[type][index]-self.data[type][index+days]
        else:
            if(index+days>=self.data.shape[0] or days<1):
                return None
            else:
                return self.data[type][index]-self.data[type][index+days]

    def get_BOP(self, index, days):
        if(self.__precomputed!=[]):
            if("BOP" + str(days) + "NONE" + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["BOP" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["BOP" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+days>=self.data.shape[0] or days<1):
                    return None
                else:
                    sum = 0
                    for x in range(0,days):
                        sum = sum + (self.data["CLOSE"][index+x]-self.data["OPEN"][index+x])/(self.data["HIGH"][index+x]-self.data["LOW"][index+x])
                    sum = sum/days
                    return sum
        else:
            if(index+days>=self.data.shape[0] or days<1):
                return None
            else:
                sum = 0
                for x in range(0,days):
                    sum = sum + (self.data["CLOSE"][index+x]-self.data["OPEN"][index+x])/(self.data["HIGH"][index+x]-self.data["LOW"][index+x])
                sum = sum/days
                return sum

    def get_CCI(self, index, days):
        if(self.__precomputed!=[]):
            if("CCI" + str(days) + "NONE" + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["CCI" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["CCI" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+days*2>self.data.shape[0] or days<2):
                    return None
                else:
                    typicals = np.zeros(days)
                    for x in range(0,days):
                        sum = 0
                        for y in range(0,days):
                            sum = sum + (self.data["CLOSE"][index+x+y] + self.data["LOW"][index+x+y] + self.data["HIGH"][index+x+y])/3
                        typicals[x] = sum
                    MA = typicals.sum()/days
                    meanDev = 0
                    for x in range(0,days):
                        meanDev = meanDev + abs(typicals[x] - MA)
                    meanDev = meanDev/days
                    return (typicals[0]-MA)/(0.015*meanDev)
        else:
            if(index+days*2>self.data.shape[0] or days<2):
                return None
            else:
                typicals = np.zeros(days)
                for x in range(0,days):
                    sum = 0
                    for y in range(0,days):
                        sum = sum + (self.data["CLOSE"][index+x+y] + self.data["LOW"][index+x+y] + self.data["HIGH"][index+x+y])/3
                    typicals[x] = sum
                MA = typicals.sum()/days
                meanDev = 0
                for x in range(0,days):
                    meanDev = meanDev + abs(typicals[x] - MA)
                meanDev = meanDev/days
                return (typicals[0]-MA)/(0.015*meanDev)

    def get_CMO(self, index, days):
        if(self.__precomputed!=[]):
            if("CMO" + str(days) + "NONE" + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["CMO" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["CMO" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+days>=self.data.shape[0] or days<1):
                    return None
                else:
                    su = 0
                    sd = 0
                    for x in range(0,days):
                        if(self.data["CLOSE"][index+x+1]<self.data["CLOSE"][index+x]):
                            su = su + self.data["CLOSE"][index+x] - self.data["CLOSE"][index+x+1]
                        if(self.data["CLOSE"][index+x+1]>self.data["CLOSE"][index+x]):
                            sd = sd + self.data["CLOSE"][index+x+1] - self.data["CLOSE"][index+x]
                    return 100*((su-sd)/(su+sd))
        else:
            if(index+days>=self.data.shape[0] or days<1):
                return None
            else:
                su = 0
                sd = 0
                for x in range(0,days):
                    if(self.data["CLOSE"][index+x+1]<self.data["CLOSE"][index+x]):
                        su = su + self.data["CLOSE"][index+x] - self.data["CLOSE"][index+x+1]
                    if(self.data["CLOSE"][index+x+1]>self.data["CLOSE"][index+x]):
                        sd = sd + self.data["CLOSE"][index+x+1] - self.data["CLOSE"][index+x]
                return 100*((su-sd)/(su+sd))

    def get_ROC(self, index, days):
        if(self.__precomputed!=[]):
            if("ROC" + str(days) + "NONE" + "NONE" + "NONE" + "NONE" in self.__precomputed):
                if(np.isnan(self.data["ROC" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index])):
                    return None
                else:
                    return self.data["ROC" + str(days) + "NONE" + "NONE" + "NONE" + "NONE"][index]
            else:
                if(index+days>=self.data.shape[0] or days<1):
                    return None
                else:
                    return 100*(self.data["CLOSE"][index]-self.data["CLOSE"][index+days])/self.data["CLOSE"][index+days]
        else:
            if(index+days>=self.data.shape[0] or days<1):
                return None
            else:
                return 100*(self.data["CLOSE"][index]-self.data["CLOSE"][index+days])/self.data["CLOSE"][index+days]
