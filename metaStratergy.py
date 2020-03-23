# TODO: Implement multi core functionality

from datetime import datetime
from dataLoader import dataLoader
from stratergy import stratergy
import sys
import numpy as np
import matplotlib.pyplot as plt
class metaStratergy:
    def __init__(self, everyMinute=None, everyHour=None, everyDay=None, everyWeek=None, everyMonth=None, everyYear=None):
        if(callable(everyDay)!=True and everyDay!=None):
            print("everyDay must be a function")
            sys.exit()
        if(callable(everyMinute)!=True and everyMinute!=None):
            print("everyMinute must be a function")
            sys.exit()
        if(callable(everyHour)!=True and everyHour!=None):
            print("everyHour must be a function")
            sys.exit()
        if(callable(everyMonth)!=True and everyMonth!=None):
            print("everyHour must be a function")
            sys.exit()
        if(callable(everyYear)!=True and everyYear!=None):
            print("everyYear must be a function")
            sys.exit()
        self.everyYear = everyYear
        self.everyMonth = everyMonth
        self.everyWeek = everyWeek
        self.everyDay = everyDay
        self.everyMinute =  everyMinute
        self.everyHour = everyHour


    def runTest(self, dataLoaders=[], stratergies=[], verbose=1, startingCapital=100000):

        if(len(dataLoaders)!=len(stratergies)):
            print("dataLoaders list must have the same length as the stratergies list")
            sys.exit()

        for x in range(0,len(dataLoaders)):
            if(type(dataLoaders[x])!=dataLoader):
                print("dataLoaders list must only contain dataLoader objects")
                sys.exit()
            if(type(stratergies[x])!=stratergy):
                print("stratergies list must only contain stratergy objects")
                sys.exit()

        print("Running test ...")

        self.stratergies = stratergies
        self.dataLoaders = dataLoaders
        latestStartDate = 0
        earliestFinishDate = 0
        for x in range(0,len(dataLoaders)):
            data = dataLoaders[x].data
            if(x==0):
                latestStartDate = data["Date"][data.shape[0]-3]
                earliestFinishDate = data["Date"][0]
            if(data["Date"][0]<earliestFinishDate):
                earliestFinishDate = data["Date"][0]
            if(data["Date"][data.shape[0]-3]>latestStartDate):
                latestStartDate = data["Date"][data.shape[0]-3]
        print(latestStartDate)
        print(earliestFinishDate)
        startingIndexs = np.zeros(len(dataLoaders))
        for y in range(0,len(dataLoaders)):
            found = False
            x = 0
            while(found==False):
                if(dataLoaders[y].data["Date"][x]==latestStartDate):
                    startingIndexs[y] = x
                    found=True
                x = x + 1

        endingIndexs = np.zeros(len(dataLoaders))
        for y in range(0,len(dataLoaders)):
            found = False
            x = 0
            while(found==False):
                if(dataLoaders[y].data["Date"][x]==earliestFinishDate):
                    endingIndexs[y] = x
                    found=True
                x = x + 1
        self.datePlot = dataLoaders[0].data["Date"]
        self.datePlot = self.datePlot[int(endingIndexs[0]):int(startingIndexs[0])]
        self.datePlot = self.datePlot.values[::-1]
        for x in range(len(dataLoaders)):
            if(endingIndexs[x]-startingIndexs[x]!=endingIndexs[0]-startingIndexs[0]):
                print("data missing in dataLoader "+str(x))
                sys.exit()

        for x in range(len(dataLoaders)):
            stratergies[x].testData = dataLoaders[x]
            stratergies[x].currentIndex = int(startingIndexs[x])
            stratergies[x].startingIndex = int(startingIndexs[x])
            stratergies[x].startingCapital = startingCapital/len(dataLoaders)
            stratergies[x].testMoney = startingCapital/len(dataLoaders)
            stratergies[x].testStock = 0
            stratergies[x].meta = True
            stratergies[x].verbose = verbose
        self.benchmarkPlot = np.zeros(int(startingIndexs[0]-endingIndexs[0]))
        self.stratPlot = np.zeros(int(startingIndexs[0]-endingIndexs[0]))
        for x in range(0,int(startingIndexs[0]-endingIndexs[0])):
            self.nextDay()
            for y in range(0,len(dataLoaders)):
                if(stratergies[y].testMoney>0 or stratergies[y].testStock>0):
                    stratergies[y].nextDay()
                else:
                    stratergies[y].currentIndex = stratergies[y].currentIndex - 1
            self.stratPlot[x] = self.get_TOTALCAPITAL()
            self.benchmarkPlot[x] = self.get_BENCHMARK()
        totalStratProfit = 0
        totalStratProfit = self.get_TOTALCAPITAL()
        percentageStratProfit = ((totalStratProfit-startingCapital)/startingCapital)*100
        print("Percentage change : "+str(percentageStratProfit)+"%   Benchmark : "+str(100*(self.benchmarkPlot[self.benchmarkPlot.shape[0]-1]-startingCapital)/startingCapital)+"%")

    def nextDay(self):
        self.doYear()
        self.doMonth()
        self.doWeek()
        self.doDay()
        self.doHour()
        self.doMin()

    def doYear(self):
        if(self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].year>self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].year):
            # Carry out the function here
            if(self.everyYear!=None):
                self.everyYear(self)
            return False
        else:
            return True

    def doMonth(self):
        if(self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].month>self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].month or self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].month<0.5*self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].month):
            # Carry out the function here
            if(self.everyMonth!=None):
                self.everyMonth(self)
            return False
        else:
            return True

    def doWeek(self):
        if(self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].weekday()==1 and self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].weekday()!=1):
            # Carry out the function here
            if(self.everyWeek!=None):
                self.everyWeek(self)
                return False
            else:
                return True

    def doDay(self):
        if(self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].day>self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].day or self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].day<0.5*self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].day):
            # Carry out the function here
            if(self.everyDay!=None):
                self.everyDay(self)
            return False
        else:
            return True

    def doHour(self):
        if(self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].hour>self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].hour or self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].hour<0.5*self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].hour):
            # Carry out the function here
            if(self.everyHour!=None):
                self.everyHour(self)
            return False
        else:
            return True

    def doMin(self):
        if(self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].minute>self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].minute or self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex].minute<0.5*self.stratergies[0].testData.data["Date"][self.stratergies[0].currentIndex+1].minute):
            # Carry out the function here
            if(self.everyMin!=None):
                self.everyMin(self)
            return False
        else:
            return True

    def plot(self):
        plt.plot(self.datePlot, self.benchmarkPlot)
        plt.plot(self.datePlot, self.stratPlot)
        plt.show()

    def get_Data(self, stratNumber, days):
        return self.stratergies[stratNumber].get_DATA(days)

    def rebalanceAndLiquidate(self,splitList):
        if(len(splitList)!=len(self.dataLoaders)):
            print("splitList of incorrect length")
            sys.exit()
        total = 0
        for split in splitList:
            total = total + split
        if(total!=1):
            print("splitList items must add to 1")
            sys.exit()
        total = self.get_TOTALCAPITAL()
        x = 0
        for strat in self.stratergies:
            if(strat.get_STOCKCOUNT()!=0):
                strat.sell(strat.get_STOCKCOUNT())
            strat.testMoney = splitList[x]*total
            x = x + 1

    def rebalanceAvailibleCapital(self,splitList):
        if(len(splitList)!=len(self.dataLoaders)):
            print("splitList of incorrect length")
            sys.exit()
        total = 0
        for split in splitList:
            total = total + split
        if(total<0.999999999 or total>1.00000001):
            print("splitList items must add to 1")
            sys.exit()
        total = self.get_AVALIABLECAPITAL()
        x = 0
        for strat in self.stratergies:
            strat.testMoney = splitList[x]*total
            x = x + 1

    def get_TOTALCAPITAL(self):
        runningTotal = 0
        for strat in self.stratergies:
            runningTotal = runningTotal + strat.get_TOTALCAPITAL()
        return runningTotal

    def get_AVALIABLECAPITAL(self):
        runningTotal = 0
        for strat in self.stratergies:
            runningTotal = runningTotal + strat.get_AVALIABLECAPITAL()
        return runningTotal

    def get_BENCHMARK(self):
        runningTotal = 0
        for strat in self.stratergies:
            runningTotal = runningTotal + strat.get_BENCHMARK()
        return runningTotal
