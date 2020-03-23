# import warnings filter
from warnings import simplefilter
# ignore all future warnings
simplefilter(action='ignore', category=FutureWarning)
simplefilter(action='ignore', category=PendingDeprecationWarning)
simplefilter(action='ignore', category=DeprecationWarning)
import numpy as np
import math as math
from numpy import genfromtxt
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import BatchNormalization
import csv
import tensorflow as tf
from keras.backend import manual_variable_initialization
from keras import optimizers

manual_variable_initialization(False)
class Predictor:

    def __init__(self, attributes, answers, learningRate):

        self.trainingData = attributes
        self.trainingAnswers = answers
        self.learningRate = learningRate
        self.model = Sequential()
        self.model.add(Dense(13, activation='relu', input_shape=(attributes[0].shape[0],), use_bias=True))
        self.model.add(Dense(13, activation='relu', use_bias=True))
        # self.model.add(Dropout(0.1, noise_shape=None, seed=None))
        self.model.add(Dense(13, activation='relu', use_bias=True))
        self.model.add(Dense(13, activation='relu', use_bias=True))
        self.model.add(Dense(5, activation='relu', use_bias=True))
        self.model.add(Dense(1, activation='sigmoid'))

    def train(self, filePath):
        adam = optimizers.Adam(lr=self.learningRate*2, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=True)
        self.model.compile(loss='binary_crossentropy', optimizer=adam, metrics=['accuracy'])
        self.model.fit(self.trainingData, self.trainingAnswers,epochs=500,batch_size=32,verbose=1)
        # accuracy = 100
        # while(accuracy==100):
        #     self.model.compile(loss='mean_squared_logarithmic_error', optimizer=adam, metrics=['mae'])
        #     self.model.fit(self.trainingData, self.trainingAnswers,epochs=100,batch_size=32,verbose=1)
        #     accuracy = self.model.evaluate(self.trainingData, self.trainingAnswers)[1]
        #     print(accuracy)
        self.model.save(filePath)

    def load(self, filePath):
        self.model.load_weights(filePath)
        adam = optimizers.Adam(lr=self.learningRate, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=True)
        self.model.compile(loss='mean_squared_logarithmic_error', optimizer=adam, metrics=['mae'])

    def predictOne(self, values):
        return self.model.predict(values)


    def predictionAccuracy(self):
        return self.model.evaluate(self.testData, self.testAnswers)
