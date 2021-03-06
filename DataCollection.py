import requests
import pandas as pd
import numpy as np
import datetime

startDate = datetime.datetime(2019, 8, 10)
endDate = datetime.datetime(2019, 8, 20)

print(startDate)
print(endDate)


stations = pd.DataFrame(data=requests.post('https://api.hypr.cl/station',headers = {
        'x-api-key': "iQ0WKQlv3a7VqVSKG6BlE9IQ88bUYQws6UZLRs1B",
        'command': "list",
        'Accept': "*/*", 'Cache-Control': "no-cache",
        'Accept-Encoding': "gzip, deflate",
        'Content-Length': "0",
        'Connection': "keep-alive",
    }).json()["list"])

print(stations)

currentDate = startDate
frame = datetime.timedelta(seconds = 1)
increment = datetime.timedelta(minutes = 2)
result = []
while (endDate > currentDate):

    request = requests.post('https://api.hypr.cl/raw',headers = {
            'x-api-key': "iQ0WKQlv3a7VqVSKG6BlE9IQ88bUYQws6UZLRs1B",
            'time_start': currentDate.isoformat() + "z",
            'time_stop': (currentDate + frame).isoformat() + "z",
            'command': "list",
            'Accept': "*/*", 'Cache-Control': "no-cache",
            'Accept-Encoding': "gzip, deflate",
            'Content-Length': "0",
            'Connection': "keep-alive",
        })
    print(currentDate)
    print("Status code: %d, size: %fmb" % (request.status_code, len(request.content) / 1000000.0))
    if (request.status_code != 200):
        print(request.content)
        continue

    raw = pd.DataFrame(data=request.json()["raw"])

    counts = raw["serial"].value_counts()
    buffer = [currentDate]
    for label in stations["serial"]:
        buffer.append(len(raw[raw["serial"]==label]))
    result.append(buffer)

    currentDate += increment

resultDataframe = pd.DataFrame(result, columns=(np.concatenate([["time"], stations["serial"].values])))


resultDataframe.to_csv("visitorCount1_2.csv")
stations.to_csv("stations.csv")
