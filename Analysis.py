import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as seabornInstance
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn import metrics
from sklearn.preprocessing import PolynomialFeatures
from statsmodels.tsa.api import ExponentialSmoothing, SimpleExpSmoothing, Holt
from sklearn.metrics import mean_squared_error
from sklearn.feature_selection import RFE
from sklearn.svm import SVR
import copy
from sklearn.utils.testing import ignore_warnings
from sklearn.exceptions import ConvergenceWarning
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OneHotEncoder


seasonalPeriod = 720
testingSize = 720
#visitorTimelambda = lambda x: x.minute == 0 or x.minute == 30
visitorTimelambda = lambda x: x.minute % 2 == 0
weatherFactors = ['Air temperature (degC)','Horizontal visibility (m)','Wind speed (m/s)', 'Relative humidity (%)', 'Cloud amount (1/8)', 'weekend']

visitor = pd.read_csv("visitorCount10_2.csv")
visitor['time'] = [pd.to_datetime(item) for item in visitor['time']]
stations = pd.read_csv("stations.csv")

stations = stations[stations['serial'].apply(lambda x: x in ['000000000f4919c9', '0000000019fb59c4', '00000000342570c2', '0000000038bf9618', '0000000038d83d41', '0000000053c6c2be', '000000006b087f40', '000000007b5207b6', '00000000a53ed894', '00000000aa852af1', '00000000afef4555', '00000000fb7600be', '00000000fdda10fe', '00000000fffb8cf0'])]

weather = pd.read_csv("Helsinki_weather_data.csv")

for label in stations['serial']:
    visitor[label] = visitor[label] / 10.0


addingRows = []
for row in weather.values:
    for i in range(5):
        newRow = copy.deepcopy(row)
        newRow[3] = newRow[3][:-1] + str(i * 2)
        addingRows.append(newRow)
weather = pd.DataFrame(data=addingRows, columns=weather.columns)

weather['dateTime'] = [pd.datetime(year=int(weather.at[i,'Year']), month=int(weather.at[i,'m']), day=int(weather.at[i,'d']), hour=int(weather.at[i,'Time'][0:2]), minute=int(weather.at[i,'Time'][-2:len(weather.at[i,'Time'])])) for i in weather.index]
weather = weather.loc[weather['dateTime'] >= visitor.at[0, "time"]]
weather = weather.loc[weather['dateTime'] <= visitor.at[len(visitor.index) - 1, "time"]]
weather = weather[weather['dateTime'].apply(visitorTimelambda)]
weather['weekend'] = [0 if item.weekday() < 5 else 1 for item in weather['dateTime']]
weather.fillna(0, inplace = True)

@ignore_warnings(category=ConvergenceWarning)
def train(target):
    holtWinterStation = [target]
    """    holtWinterStation = ['0000000019fb59c4', '00000000342570c2', '0000000038bf9618', '0000000053c6c2be', '000000006b087f40', '000000007b5207b6', '00000000aa852af1', '00000000fffb8cf0']
    if (not target in holtWinterStation):
        holtWinterStation.append(target)
    """
    #trainX = (visitor[target][:-testingSize]).ewm(span = 100, adjust=False).mean()

    holtWinterModelsFit3 = []
    for label in holtWinterStation:
        fit3 = ExponentialSmoothing((visitor[label][:-testingSize])+1, seasonal_periods=seasonalPeriod, trend='add', seasonal='add', damped=True).fit(use_boxcox=True)
        holtWinterModelsFit3.append(fit3)


    trainX = (visitor[target][:-testingSize])

    resultDataDict = {}
    for i in range(len(holtWinterStation)):
        resultDataDict[holtWinterStation[i] + "2"] = holtWinterModelsFit3[i].predict(start=0, end=len(visitor.index)-testingSize - 1) - 1

    for factor in weatherFactors:
        resultDataDict[factor] = weather[factor][:len(weather.index)-testingSize].values

    features = pd.DataFrame(data=resultDataDict)

    poly = PolynomialFeatures(degree = 3)
    polyX = poly.fit_transform(features.values, y=visitor[target][:-testingSize])

    #regressor = SVR(kernel="poly", coef0=0.0, degree=2)
    regressor = LinearRegression()
    rfe = RFE(regressor, n_features_to_select=None, step=1)
    rfe = rfe.fit(polyX, visitor[target][:-testingSize])


    predictDataDict = {}
    holtWinterPredict = []
    for i in range(len(holtWinterStation)):
        predictDataDict[holtWinterStation[i] + "2"] = holtWinterModelsFit3[i].predict(start=len(visitor.index)-testingSize, end=len(visitor.index)) - 1

    for factor in weatherFactors:
        predictDataDict[factor] = weather[factor][-testingSize - 1:].values

    testFeatures = pd.DataFrame(data=predictDataDict)
    polyTestX = poly.transform(testFeatures.values)

    return rfe.predict(polyTestX)


sum = 0
best = 1000000000
bestLabel = ""
goodWorking = []
convergent = []
count = len(stations['serial'])
for label in stations['serial']:
    print(label)
    try:
        prediction = train(label)
        error = mean_squared_error(prediction, visitor[label][-testingSize - 1:])
        print(error)
        sum += error
        if (error == 0):
            count -= 1
        else:
            if (error < best):
                best = error
                bestLabel = label
            if (error < 50.0):
                goodWorking.append(label)

        pd.DataFrame(data={"prediction" : prediction, "actual": visitor[label][-testingSize - 1:]}).to_csv("%sPrediction.csv" % (label), index = False)
        convergent.append(label)
    except Exception as e:
        count -= 1
        print("failed")
        print(e)
    print("")

print("Average is %f on %d, best is %s at %f" % (sum / count, count, bestLabel, best))
print(goodWorking)
print(convergent)
