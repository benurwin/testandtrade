from testandtrade.dataloader import dataloader
# from cfd import cfd
import numpy as np
import math
import sys
import time
import copy
import threading
import inspect
import warnings
from types import MethodType
import numbers
from datetime import timedelta
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

class strategy:

    # Adds the functions for the stratergy
    def __init__(self, stratName, everyDayOpen=None, everyDayClose=None, everyWeek=None, everyMonth=None, everyYear=None, verbose=1):
        if(type(stratName)!=str):
            raise ValueError("stratName must be a string.")
        if(inspect.isfunction(everyDayOpen)!=True and everyDayOpen!=None):
            raise ValueError("everyDayOpen must be a function.")
        if(inspect.isfunction(everyDayClose)!=True and everyDayClose!=None):
            raise ValueError("everyDayClose must be a function.")
        if(inspect.isfunction(everyWeek)!=True and everyWeek!=None):
            raise ValueError("everyWeek must be a function.")
        if(inspect.isfunction(everyMonth)!=True and everyMonth!=None):
            raise ValueError("everyMonth must be a function.")
        if(inspect.isfunction(everyYear)!=True and everyYear!=None):
            raise ValueError("everyYear must be a function.")
        self.__everyYear = everyYear
        self.__everyMonth = everyMonth
        self.__everyWeek = everyWeek
        self.__everyDayOpen = everyDayOpen
        self.__everyDayClose = everyDayClose
        self.__stratName = stratName
        self.testMode = False
        self.__verbose = verbose
        self.__original_dict__ = copy.deepcopy(self.__dict__)

    # Runs a test for the stratergy
    def runTest(self, data=None, verbose=None, startingCapital=100000, plot=False, report=False, feeType=None, fee=None, overDraft=True):
        # input checking
        if(verbose==None):
            verbose=self.__verbose
        if(type(data)!=dataloader):
            raise ValueError("data parameter must be a dataloader object.")
        if(isinstance(startingCapital, numbers.Number)==False):
            raise ValueError("startingCapital must be a number.")


        if(verbose>0):
            print("Running test")

        # initialise variables
        self.__startingIndex = data.data.shape[0]-2
        self.__startingCapital = startingCapital
        self.currentCapital = startingCapital
        self.__currentIndex = self.__startingIndex
        self.__testData = data
        self.__currentFunction = None
        self.currentStockPossition = 0
        self.__openCFDs = {}
        self.__closedCFDs = []
        self.__CFDNumber = 0
        if(self.__testData.fundamentals is None):
            self.__fundamentalsNumber = None
        else:
            self.__fundamentalsNumber = data.fundamentals.shape[0]-1

        # sets up buy and sell functions
        if(feeType==None or (feeType.upper()!="PERCENTAGE" and feeType.upper()!="FLAT")):
            if(overDraft==True):
                # Carries out a buy order
                def buy(self, quantity):
                    if(quantity>0):
                        self.currentStockPossition = self.currentStockPossition + quantity
                        if(self.__currentFunction=="dc"):
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["CLOSE"][self.__currentIndex]
                        else:
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["OPEN"][self.__currentIndex]

                # carries out a sell order
                def sell(self, quantity):
                    if(quantity>0):
                        if(self.currentStockPossition<=0):
                            return
                        if(self.currentStockPossition<quantity):
                            quantity = self.currentStockPossition
                        self.currentStockPossition = self.currentStockPossition - quantity
                        if(self.__currentFunction=="dc"):
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["CLOSE"][self.__currentIndex]
                        else:
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["OPEN"][self.__currentIndex]
            else:
                # Carries out a buy order
                def buy(self, quantity):
                    if(quantity>0):
                        if(self.__currentFunction=="dc"):
                            if(quantity*self.__testData.data["CLOSE"][self.__currentIndex]>self.currentCapital):
                                quantity = self.currentCapital/self.__testData.data["CLOSE"][self.__currentIndex]
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["CLOSE"][self.__currentIndex]
                        else:
                            if(quantity*self.__testData.data["OPEN"][self.__currentIndex]>self.currentCapital):
                                quantity = self.currentCapital/self.__testData.data["OPEN"][self.__currentIndex]
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["OPEN"][self.__currentIndex]
                        self.currentStockPossition = self.currentStockPossition + quantity
                    if(self.currentCapital<0.000001):
                        self.currentCapital = 0

                # carries out a sell order
                def sell(self, quantity):
                    if(quantity>0):
                        if(self.currentStockPossition<=0):
                            return
                        if(self.currentStockPossition<quantity):
                            quantity = self.currentStockPossition
                        self.currentStockPossition = self.currentStockPossition - quantity
                        if(self.__currentFunction=="dc"):
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["CLOSE"][self.__currentIndex]
                        else:
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["OPEN"][self.__currentIndex]
                    if(self.currentCapital<0.000001):
                        self.currentCapital = 0

        elif(feeType.upper()=="PERCENTAGE"):
            if(overDraft==True):
                # Carries out a buy order
                def buy(self, quantity):
                    if(quantity>0):
                        self.currentStockPossition = self.currentStockPossition + quantity
                        if(self.__currentFunction=="dc"):
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["CLOSE"][self.__currentIndex] - quantity*self.__testData.data["CLOSE"][self.__currentIndex]*fee
                        else:
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["OPEN"][self.__currentIndex] - quantity*self.__testData.data["OPEN"][self.__currentIndex]*fee

                # carries out a sell order
                def sell(self, quantity):
                    if(quantity>0):
                        if(self.currentStockPossition<=0):
                            return
                        if(self.currentStockPossition<quantity):
                            quantity = self.currentStockPossition
                        self.currentStockPossition = self.currentStockPossition - quantity
                        if(self.__currentFunction=="dc"):
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["CLOSE"][self.__currentIndex] - quantity*self.__testData.data["CLOSE"][self.__currentIndex]*fee
                        else:
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["OPEN"][self.__currentIndex] - quantity*self.__testData.data["OPEN"][self.__currentIndex]*fee
            else:
                # Carries out a buy order
                def buy(self, quantity):
                    if(quantity>0):
                        if(self.__currentFunction=="dc"):
                            if(quantity*self.__testData.data["CLOSE"][self.__currentIndex]*fee+quantity*self.__testData.data["CLOSE"][self.__currentIndex]>self.currentCapital):
                                quantity = self.currentCapital/(self.__testData.data["CLOSE"][self.__currentIndex]*fee+self.__testData.data["CLOSE"][self.__currentIndex])
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["CLOSE"][self.__currentIndex] - quantity*self.__testData.data["CLOSE"][self.__currentIndex]*fee
                        else:
                            if(quantity*self.__testData.data["OPEN"][self.__currentIndex]*fee+quantity*self.__testData.data["OPEN"][self.__currentIndex]>self.currentCapital):
                                quantity = self.currentCapital/(self.__testData.data["OPEN"][self.__currentIndex]*fee+self.__testData.data["OPEN"][self.__currentIndex])
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["OPEN"][self.__currentIndex] - quantity*self.__testData.data["OPEN"][self.__currentIndex]*fee
                        self.currentStockPossition = self.currentStockPossition + quantity
                    if(self.currentCapital<0.000001):
                        self.currentCapital = 0

                # carries out a sell order
                def sell(self, quantity):
                    if(quantity>0):
                        if(self.currentStockPossition<=0):
                            return
                        if(self.currentStockPossition<quantity):
                            quantity = self.currentStockPossition
                        self.currentStockPossition = self.currentStockPossition - quantity
                        if(self.__currentFunction=="dc"):
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["CLOSE"][self.__currentIndex] - quantity*self.__testData.data["CLOSE"][self.__currentIndex]*fee
                        else:
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["OPEN"][self.__currentIndex] - quantity*self.__testData.data["OPEN"][self.__currentIndex]*fee
                    if(self.currentCapital<0.000001):
                        self.currentCapital = 0
        elif(feeType.upper()=="FLAT"):
            if(overDraft==True):
                # Carries out a buy order
                def buy(self, quantity):
                    if(quantity>0):
                        self.currentStockPossition = self.currentStockPossition + quantity
                        if(self.__currentFunction=="dc"):
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["CLOSE"][self.__currentIndex] - fee
                        else:
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["OPEN"][self.__currentIndex] - fee

                # carries out a sell order
                def sell(self, quantity):
                    if(quantity>0):
                        if(self.currentStockPossition<=0):
                            return
                        if(self.currentStockPossition<quantity):
                            quantity = self.currentStockPossition
                        self.currentStockPossition = self.currentStockPossition - quantity
                        if(self.__currentFunction=="dc"):
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["CLOSE"][self.__currentIndex] - fee
                        else:
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["OPEN"][self.__currentIndex] - fee
            else:
                # Carries out a buy order
                def buy(self, quantity):
                    if(quantity>0):
                        if(self.__currentFunction=="dc"):
                            if(quantity*self.__testData.data["CLOSE"][self.__currentIndex]+fee>self.currentCapital):
                                quantity = max((self.currentCapital-fee)/(self.__testData.data["CLOSE"][self.__currentIndex]), 0)
                            if(quantity==0):
                                return
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["CLOSE"][self.__currentIndex] - fee
                        else:
                            if(quantity*self.__testData.data["OPEN"][self.__currentIndex]+fee>self.currentCapital):
                                quantity = max((self.currentCapital-fee)/(self.__testData.data["OPEN"][self.__currentIndex]), 0)
                            if(quantity==0):
                                return
                            self.currentCapital = self.currentCapital - quantity*self.__testData.data["OPEN"][self.__currentIndex] - fee
                        self.currentStockPossition = self.currentStockPossition + quantity
                    if(self.currentCapital<0.000001):
                        self.currentCapital = 0

                # carries out a sell order
                def sell(self, quantity):
                    if(quantity>0):
                        if(self.currentStockPossition<=0):
                            return
                        if(self.currentStockPossition<quantity):
                            quantity = self.currentStockPossition
                        self.currentStockPossition = self.currentStockPossition - quantity
                        if(self.__currentFunction=="dc"):
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["CLOSE"][self.__currentIndex] - fee
                        else:
                            self.currentCapital = self.currentCapital + quantity*self.__testData.data["OPEN"][self.__currentIndex] - fee
                    if(self.currentCapital<0.000001):
                        self.currentCapital = 0
        self.buy = MethodType(buy, self)
        self.sell = MethodType(sell, self)

        # sets up the functions to be ran each day
        functions = []
        if(self.__everyYear!=None):
            functions.append(self.__doYear)
        if(self.__everyMonth!=None):
            functions.append(self.__doMonth)
        if(self.__everyWeek!=None):
            functions.append(self.__doWeek)
        if(self.__everyDayOpen!=None):
            functions.append(self.__doDayOpen)
        if(self.__everyDayClose!=None):
            functions.append(self.__doDayClose)

        # progress bar set up
        if(verbose>0):
            self.__progressBarPoints = []
            self.__progressBarPointer = 0
            self.__progressBarPoints.append(self.__startingIndex)
            split = math.floor(self.__testData.data.shape[0]/20)
            x=19
            while(x>-1):
                self.__progressBarPoints.append(split*x)
                x=x-1
            def progressBar(self):
                if(self.__currentIndex==self.__progressBarPoints[self.__progressBarPointer]):
                    sys.stdout.write('\r')
                    # the exact output you're looking for:
                    sys.stdout.write("[%-80s] %d%%" % ('='*(4*self.__progressBarPointer-1)+">", 5*self.__progressBarPointer))
                    sys.stdout.flush()
                    self.__progressBarPointer = self.__progressBarPointer + 1

        # runs the test
        if(plot==True or report==True or self.testMode==True):
            stratData = []
            buyPoints = []
            if(verbose>0):
                while(self.__currentIndex>=0):
                    progressBar(self)
                    stock = self.currentStockPossition
                    for funct in functions:
                        funct()
                    if(stock==self.currentStockPossition):
                        buyPoints.append("")
                    elif(stock<self.currentStockPossition):
                        buyPoints.append("B")
                    else:
                        buyPoints.append("S")
                    self.__currentFunction="dc"
                    stratData.append(self.get_TOTALCAPITAL())
                    self.__currentIndex = self.__currentIndex - 1
            else:
                while(self.__currentIndex>=0):
                    stock = self.currentStockPossition
                    for funct in functions:
                        funct()
                    if(stock==self.currentStockPossition):
                        buyPoints.append("")
                    elif(stock<self.currentStockPossition):
                        buyPoints.append("B")
                    else:
                        buyPoints.append("S")
                    self.__currentFunction="dc"
                    stratData.append(self.get_TOTALCAPITAL())
                    self.__currentIndex = self.__currentIndex - 1
        else:
            if(verbose>0):
                while(self.__currentIndex>=0):
                    progressBar(self)
                    for funct in functions:
                        funct()
                    # do plotting assignmets
                    self.__currentIndex = self.__currentIndex - 1
            else:
                while(self.__currentIndex>=0):
                    for funct in functions:
                        funct()
                    # do plotting assignmets
                    self.__currentIndex = self.__currentIndex - 1

        if(verbose!=0):
            print()

        # spins up another thread to handle the plotting and reporting
        if((plot==True or report==True) and self.testMode==False):
            self.__plot(stratData, self.__testData, buyPoints, plot, report)


        if(self.testMode==True):
            holder = stratData[::-1]
        else:
            self.__currentIndex = self.__currentIndex + 1           #because of df having a zero index
            holder = self.get_TOTALCAPITAL()/self.__startingCapital

        # Clear all data so it can be ran again
        self.__dict__ = self.__original_dict__
        self.__original_dict__ = copy.deepcopy(self.__dict__)
        return holder


    # helper function of runTest that plots data in a dash app
    def __plot(self, stratData, testData, buyPoints, plot, report):

        dates = list(testData.data["DATE"][:self.__startingIndex+1])
        stockData = list(testData.data["CLOSE"][:self.__startingIndex+1])
        stratData=stratData[::-1]
        if(plot==True):
            stratData[:] = [x / stratData[len(stockData)-1] for x in stratData]
            stockData[:] = [x / stockData[len(stockData)-1] for x in stockData]
            plt.plot(dates, stratData, '-', label=self.__stratName)
            plt.plot(dates, stockData, '-', label=self.__testData.info()[0])
            plt.legend()
            plt.show()
        if(report==True):
            if(self.__isnotebook()==True):
                import pyfolio as pf
                stratData = stratData[::-1]
                dates = dates[::-1]
                stockData = stockData[::-1]
                stratData[1:] = [(stratData[x] - stratData[x-1]) / stratData[x-1] for x in range(1,len(stratData))]
                stratData[0] = 0
                stockData[1:] = [(stockData[x] - stockData[x-1]) / stockData[x-1] for x in range(1,len(stockData))]
                stockData[0] = 0
                df1 = pd.DataFrame(stratData, dates)
                df1= df1[0]
                df2 = pd.DataFrame(stockData, dates)
                df2= df2[0]
                df2 = df2.rename(self.__testData.info()[0])
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    pf.create_full_tear_sheet(df1,benchmark_rets=df2)
            else:
                print("To generate a report testandtrade requires that the code be ran in a jupyter notebook.")

    def __isnotebook(self):
        try:
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':
                return True   # Jupyter notebook or qtconsole
            elif shell == 'TerminalInteractiveShell':
                return False  # Terminal running IPython
            else:
                return False  # Other type (?)
        except NameError:
            return False

    # The following are helper functions for runTest
    def __doYear(self,a=1):
        if(self.__testData.data["DATE"][self.__currentIndex].year>self.__testData.data["DATE"][self.__currentIndex+1].year):
            self.__currentFunction = "y"
            self.__everyYear(self)

    def __doMonth(self,a=1):
        if(self.__testData.data["DATE"][self.__currentIndex].month>self.__testData.data["DATE"][self.__currentIndex+1].month or self.__testData.data["DATE"][self.__currentIndex].month<0.5*self.__testData.data["DATE"][self.__currentIndex+1].month):
            self.__currentFunction = "m"
            self.__everyMonth(self)

    def __doWeek(self,a=1):
        if(self.__testData.data["DATE"][self.__currentIndex].week>self.__testData.data["DATE"][self.__currentIndex+1].week or self.__testData.data["DATE"][self.__currentIndex].week<0.5*self.__testData.data["DATE"][self.__currentIndex+1].week):
            self.__currentFunction = "w"
            self.__everyWeek(self)

    def __doDayOpen(self,a=1):
        self.__currentFunction = "do"
        self.__everyDayOpen(self)

    def __doDayClose(self,a=1):
        self.__currentFunction = "dc"
        self.__everyDayClose(self)



    # def openCFDPosition(self, type, quantity, leverage=1):
    #     if(self.__currentFunction!="dc"):
    #         self.__openCFDs[self.__CFDNumber] = cfd(type, quantity, leverage, self.__testData.data["Date"][self.__currentIndex], self.__testData.data["Close"][self.__currentIndex])
    #         self.__CFDNumber = self.__CFDNumber + 1
    #     else:
    #         self.__openCFDs[self.__CFDNumber] = cfd(type, quantity, leverage, self.__testData.data["Date"][self.__currentIndex], self.__testData.data["Open"][self.__currentIndex])
    #         self.__CFDNumber = self.__CFDNumber + 1
    #
    #     return self.__CFDNumber - 1
    #
    # def closeCFDPosition(self, contractNumber):
    #     if(self.__currentFunction!="dc"):
    #         cfd = self.__openCFDs.get(contractNumber)
    #         self.currentCapital = self.currentCapital + cfd.closePossition(self.__testData.data["Date"][self.__currentIndex], self.__testData.data["Close"][self.__currentIndex])
    #         self.__openCFDs.pop(contractNumber)
    #         self.__closedCFDs.append(cfd)
    #     else:
    #         cfd = self.__openCFDs.get(contractNumber)
    #         self.currentCapital = self.currentCapital + cfd.closePossition(self.__testData.data["Date"][self.__currentIndex], self.__testData.data["Open"][self.__currentIndex])
    #         self.__openCFDs.pop(contractNumber)
    #         self.__closedCFDs.append(cfd)
    #
    # def get_CFDPOSITIONS(self):
    #     out = []
    #     for key in self.__openCFDs.keys():
    #         cfd = self.__openCFDs[key]
    #         cfd = cfd.getInfo()
    #         out.append((key, cfd[0], cfd[1]))
    #     return out

    # returns liquid capital
    def get_AVALIABLECAPITAL(self):
        return self.currentCapital

    # returns total value of the strat
    def get_TOTALCAPITAL(self):
        if(self.__currentFunction=="dc"):
            # cfdVals = 0
            # for key in self.__openCFDs.keys():
            #     cfdVals = cfdVals + self.__openCFDs[key].getValue(self.__testData.data["Close"][self.__currentIndex])
            return float(self.currentCapital+self.currentStockPossition*self.__testData.data["CLOSE"][self.__currentIndex])
        else:
            # cfdVals = 0
            # for key in self.__openCFDs.keys():
            #     cfdVals = cfdVals + self.__openCFDs[key].getValue(self.__testData.data["Open"][self.__currentIndex])
            return float(self.currentCapital+self.currentStockPossition*self.__testData.data["OPEN"][self.__currentIndex])

    # returns quantity of stock held
    def get_STOCKCOUNT(self):
        return self.currentStockPossition

    # returns data of the past n days
    def get_DATA(self, numberOfDays):
        if(self.__currentFunction=="dc"):
            if(self.__currentIndex+numberOfDays<self.__testData.data.shape[0]):
                out = self.__testData.data.iloc[self.__currentIndex:self.__currentIndex+numberOfDays ,:6]
            else:
                out = self.__testData.data.iloc[self.__currentIndex:self.__testData.data.shape[0] ,:6]
            out.index = range(out.shape[0])
            return out
        else:
            if(self.__currentIndex+numberOfDays<self.__testData.data.shape[0]):
                out = self.__testData.data.iloc[self.__currentIndex:self.__currentIndex+numberOfDays ,:6]
            else:
                out = self.__testData.data.iloc[self.__currentIndex:self.__testData.data.shape[0] ,:6]
            out = out.copy()
            out.index = range(out.shape[0])
            out.at[0,"HIGH"] = None
            out.at[0,"LOW"] = None
            out.at[0,"CLOSE"] = None
            out.at[0,"VOLUME"] = None
            return out

    def get_DATAPOINT(self, dataColumn, numberOfDaysPrior=0):
        dataColumn = dataColumn.upper()
        if(self.__currentFunction=="dc"):
            if(self.__currentIndex+numberOfDaysPrior<self.__testData.data.shape[0]):
                return self.__testData.data[dataColumn][self.__currentIndex+numberOfDaysPrior]
            else:
                return None
        else:
            if(self.__currentIndex+numberOfDaysPrior<self.__testData.data.shape[0]):
                if(numberOfDaysPrior==0 and (dataColumn=="CLOSE" or dataColumn=="HIGH" or dataColumn=="LOW" or dataColumn=="VOLUME")):
                    return None
                else:
                    return self.__testData.data[dataColumn][self.__currentIndex+numberOfDaysPrior]
            else:
                return None

    def get_FUNDAMENTALDATAPOINT(self, dataColumn, numberOfPeriodsPrior=0):
        go=True
        while(go==True):
            if(self.__fundamentalsNumber-1>=0 and self.__testData.data["DATE"][self.__currentIndex]>self.__testData.fundamentals["DATE"][self.__fundamentalsNumber-1]):
                self.__fundamentalsNumber = self.__fundamentalsNumber - 1
            else:
                go=False
        if(self.__testData.data["DATE"][self.__currentIndex]>self.__testData.fundamentals["DATE"][self.__fundamentalsNumber]):
            return self.__testData.fundamentals[dataColumn][self.__fundamentalsNumber]
        else:
            return None


    # def get_FUNDAMENTALS(self, amount):
    #     return self.__testData.get_FUNDAMENTALS(self.__currentIndex, amount)

    def get_PRICE(self):
        if(self.__currentFunction=="dc"):
            return self.__testData.data["CLOSE"][self.__currentIndex]
        else:
            return self.__testData.data["OPEN"][self.__currentIndex]

    def get_FUNDAMENTALS(self):
        return self.__getFundHelper()

    def __getFundHelper(self):
        if(self.__fundamentalsNumber-1>=0 and self.__testData.data["DATE"][self.__currentIndex]>self.__testData.fundamentals["DATE"][self.__fundamentalsNumber-1]):
            self.__fundamentalsNumber = self.__fundamentalsNumber - 1
        else:
            if(self.__testData.data["DATE"][self.__currentIndex]>self.__testData.fundamentals["DATE"][self.__fundamentalsNumber]):
                out = self.__testData.fundamentals.iloc[[self.__fundamentalsNumber]]
                out.index = range(out.shape[0])
                return out
            else:
                return None

        return self.__getFundHelper()











# the following functions return tecnical indicators for the datain dataloader
    def get_SMA(self,numberOfDays, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_SMA(self.__currentIndex, numberOfDays, type)
                else:
                    return self.__testData.get_SMA(self.__currentIndex+1, numberOfDays, type)
            else:
                return self.__testData.get_SMA(self.__currentIndex, numberOfDays, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")


    def get_EMA(self, numberOfDays, smoothing=2, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_EMA(self.__currentIndex, numberOfDays, type, smoothing)
                else:
                    return self.__testData.get_EMA(self.__currentIndex+1, numberOfDays, type, smoothing)
            else:
                return self.__testData.get_EMA(self.__currentIndex, numberOfDays, type, smoothing)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and smoothing is a float double or interger if you have provided a value for it and numberOfDays is an integer.")

    def get_WMA(self, numberOfDays, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_WMA(self.__currentIndex, numberOfDays, type)
                else:
                    return self.__testData.get_WMA(self.__currentIndex+1, numberOfDays, type)
            else:
                return self.__testData.get_WMA(self.__currentIndex, numberOfDays, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")

    def get_DEMA(self, numberOfDays, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_DEMA(self.__currentIndex, numberOfDays, type)
                else:
                    return self.__testData.get_DEMA(self.__currentIndex+1, numberOfDays, type)
            else:
                return self.__testData.get_DEMA(self.__currentIndex, numberOfDays, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")

    def get_TEMA(self, numberOfDays, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_TEMA(self.__currentIndex, numberOfDays, type)
                else:
                    return self.__testData.get_TEMA(self.__currentIndex+1, numberOfDays, type)
            else:
                    return self.__testData.get_TEMA(self.__currentIndex, numberOfDays, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")

    def get_TRIMA(self, numberOfDays, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_TRIMA(self.__currentIndex, numberOfDays, type)
                else:
                    return self.__testData.get_TRIMA(self.__currentIndex+1, numberOfDays, type)
            else:
                return self.__testData.get_TRIMA(self.__currentIndex, numberOfDays, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")

    def get_KAMA(self, numberOfDays, fast=2, slow=30, type="OPEN"):
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_KAMA(self.__currentIndex, numberOfDays, type, fast, slow)
                else:
                    return self.__testData.get_KAMA(self.__currentIndex+1, numberOfDays, type, fast, slow)
            else:
                return self.__testData.get_KAMA(self.__currentIndex, numberOfDays, type, fast, slow)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")

    # # todo
    #     def get_KAMA(self, numberOfDays):
    #         this = todo
    # # todo
    #     def get_MAMA(self, numberOfDays):
    #         this = todo

    def get_VWAP(self, numberOfDays, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_VWAP(self.__currentIndex, numberOfDays, type)
                else:
                    return self.__testData.get_VWAP(self.__currentIndex+1, numberOfDays, type)
            else:
                return self.__testData.get_VWAP(self.__currentIndex, numberOfDays, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")

    def get_MACD(self, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_MACD(self.__currentIndex, type)
                else:
                    return self.__testData.get_MACD(self.__currentIndex+1, type)
            else:
                return self.__testData.get_MACD(self.__currentIndex, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string.")

    def get_MACDEXT(self, type="OPEN", funct="EMA", slow=26, fast=12):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_MACDEXT(self.__currentIndex, type, funct, slow, fast)
                else:
                    return self.__testData.get_MACDEXT(self.__currentIndex+1, type, funct, slow, fast)
            else:
                return self.__testData.get_MACDEXT(self.__currentIndex, type, funct, slow, fast)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and slow and fast are integers.")

    def get_STOCH(self):
        if(self.__currentFunction!="dc"):
            return self.__testData.get_STOCH(self.__currentIndex+1)
        else:
            return self.__testData.get_STOCH(self.__currentIndex)

    def get_RSI(self, numberOfDays, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_RSI(self.__currentIndex, numberOfDays, type)
                else:
                    return self.__testData.get_RSI(self.__currentIndex+1, numberOfDays, type)
            else:
                return self.__testData.get_RSI(self.__currentIndex, numberOfDays, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")

    def get_STOCHRSI(self, numberOfDays, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_STOCHRSI(self.__currentIndex, numberOfDays, type)
                else:
                    return self.__testData.get_STOCHRSI(self.__currentIndex+1, numberOfDays, type)
            else:
                return self.__testData.get_STOCHRSI(self.__currentIndex, numberOfDays, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")

    def get_WILLR(self, numberOfDays):
        try:
            if(self.__currentFunction!="dc"):
                return self.__testData.get_WILLR(self.__currentIndex+1, numberOfDays)
            else:
                return self.__testData.get_WILLR(self.__currentIndex, numberOfDays)
        except (KeyError, TypeError):
            raise ValueError("Check that numberOfDays is an integer.")

    # # todo
    #     def get_ADX(self, numberOfDays, type="Open"):
    #         this = todo
    # # todo
    #     def get_ADXR(self, numberOfDays, type="Open"):
    #         this = todo

    def get_APO(self, fast, slow, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_APO(self.__currentIndex, fast, slow, type)
                else:
                    return self.__testData.get_APO(self.__currentIndex+1, fast, slow, type)
            else:
                return self.__testData.get_APO(self.__currentIndex, fast, slow, type)
        except (KeyError, TypeError):
            raise ValueError("Check that fast and slow are integers and type is a valid string.")

    def get_PPO(self, type="OPEN"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_PPO(self.__currentIndex, type)
                else:
                    return self.__testData.get_PPO(self.__currentIndex+1, type)
            else:
                return self.__testData.get_PPO(self.__currentIndex, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string.")

    def get_MOM(self, numberOfDays, type="Open"):
        type = type.upper()
        try:
            if(self.__currentFunction!="dc"):
                if(type=="OPEN"):
                    return self.__testData.get_MOM(self.__currentIndex, numberOfDays, type)
                else:
                    return self.__testData.get_MOM(self.__currentIndex+1, numberOfDays, type)
            else:
                return self.__testData.get_MOM(self.__currentIndex, numberOfDays, type)
        except (KeyError, TypeError):
            raise ValueError("Check that type is a valid string and numberOfDays is an integer.")

    def get_BOP(self, numberOfDays):
        try:
            if(self.__currentFunction!="dc"):
                return self.__testData.get_BOP(self.__currentIndex+1, numberOfDays)
            else:
                return self.__testData.get_BOP(self.__currentIndex, numberOfDays)
        except (KeyError, TypeError):
            raise ValueError("Check that numberOfDays is an integer.")

    def get_CCI(self, numberOfDays):
        try:
            if(self.__currentFunction!="dc"):
                return self.__testData.get_CCI(self.__currentIndex+1, numberOfDays)
            else:
                return self.__testData.get_CCI(self.__currentIndex, numberOfDays)
        except (KeyError, TypeError):
            raise ValueError("Check that numberOfDays is an integer.")

    def get_CMO(self, numberOfDays):
        try:
            if(self.__currentFunction!="dc"):
                return self.__testData.get_CMO(self.__currentIndex+1, numberOfDays)
            else:
                return self.__testData.get_CMO(self.__currentIndex, numberOfDays)
        except (KeyError, TypeError):
            raise ValueError("Check that numberOfDays is an integer.")

    def get_ROC(self, numberOfDays):
        try:
            if(self.__currentFunction!="dc"):
                return self.__testData.get_ROC(self.__currentIndex+1, numberOfDays)
            else:
                return self.__testData.get_ROC(self.__currentIndex, numberOfDays)
        except (KeyError, TypeError):
            raise ValueError("Check that numberOfDays is an integer.")

    # def __nthroot (self, N, K):
    #     # N,K = map(float,raw_input().split())
    #     lo = 0.0
    #     hi = N
    #     mid = (lo+hi)/2
    #     while 1:
    #         mid = (lo+hi)/2
    #         if math.fabs(mid**K-N) < 1e-9:
    #             break
    #         elif mid**K < N: lo = mid
    #         else: hi = mid
    #     return mid
