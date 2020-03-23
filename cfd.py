# Plan:
# have contacts each with a reference number stored in stategy and be able to open them by creating a new contract instance
class cfd:
    def __init__(self, type, quantity, leverage, startDate, startPrice):
        self.__type = type.upper()
        self.__leverage = leverage
        self.__startDate = startDate
        self.__initialPrice = startPrice
        self.__quantity = quantity

    def closePossition(self, endDate, endPrice):
        self.__endDate = endDate
        self.__endPrice = endPrice

        if(self.__type=="LONG"):
            return (endPrice - self.__initialPrice)*self.__leverage*self.__quantity
        else:
            return (self.__initialPrice - endPrice)*self.__leverage*self.__quantity

    def getValue(self, price):
        if(self.__type=="LONG"):
            return (price - self.__initialPrice)*self.__leverage*self.__quantity
        else:
            return (self.__initialPrice - price)*self.__leverage*self.__quantity

    def getInfo(self):
        return (self.__startDate, self.__type)
