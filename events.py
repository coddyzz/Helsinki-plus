import requests
import pandas as pd
import numpy as np
import datetime

stations = pd.read_csv("stations.csv")
stations = stations[stations['serial'].apply(lambda x: x in ['000000000f4919c9', '0000000019fb59c4', '00000000342570c2', '0000000038bf9618', '0000000038d83d41', '0000000053c6c2be', '000000006b087f40', '000000007b5207b6', '00000000a53ed894', '00000000aa852af1', '00000000afef4555', '00000000fb7600be', '00000000fdda10fe', '00000000fffb8cf0'])]
visitor = pd.read_csv("visitorCount10_2.csv")
visitor['time'] = [pd.to_datetime(item) for item in visitor['time']]

startDate = visitor.at[0, "time"].tz_localize(None)
endDate = visitor.at[len(visitor.index) - 1, "time"].tz_localize(None)

print(startDate)

def getMinutes(timeDelta):
    minutes = abs(timeDelta.days) * 1440
    minutes += timeDelta.seconds // 60
    return int(minutes)


def DoEvent(row):
    result = [0] * (getMinutes(startDate - endDate) // 2)
    currentPos = 0
    lastAddition = 5435
    lastAddedOne = 0
    distance_filter = ("%f,%f,1" % (stations.at[row, "latitude"], stations.at[row, "longitude"]))
    print(distance_filter)

    while (lastAddition == 5435 and lastAddedOne < 10):
        lastAddedOne += 1
        events = requests.get("http://open-api.myhelsinki.fi/v1/events/", params={"distance_filter":distance_filter,"start":currentPos})

        for entry in events.json()["data"]:
            entryStart = pd.to_datetime(entry["event_dates"]["starting_day"])
            entryEnd = pd.to_datetime(entry["event_dates"]["ending_day"])

            if (entryStart == None or entryEnd == None):
                continue

            entryStart = entryStart.tz_localize(None)
            entryEnd = entryEnd.tz_localize(None)

            if (entryEnd < startDate or entryStart > endDate):
                continue

            entryStart = startDate if startDate > entryStart else entryStart
            entryEnd = endDate if entryEnd > endDate else entryEnd

            startPos = getMinutes(entryStart - startDate) // 2
            endPos = getMinutes(entryEnd - startDate) // 2
            lastAddedOne = 0

            for i in range(startPos, endPos):
                result[i] += 1

        lastAddition = int(events.json()["meta"]["count"])
        currentPos += lastAddition
        print(currentPos, lastAddedOne)

    return result

def DoPlace(row):
    result = [0] * (getMinutes(startDate - endDate) // 2)

    dayList = []
    currentDay = pd.to_datetime(startDate.isoformat())
    while (currentDay < endDate):
        dayList.append(currentDay)
        currentDay += datetime.timedelta(days = 1)

    currentPos = 0
    lastAddition = 5435
    lastAddedOne = 0
    distance_filter = ("%f,%f,1" % (stations.at[row, "latitude"], stations.at[row, "longitude"]))

    while (lastAddition == 5435 and lastAddedOne < 10):
        lastAddedOne += 1
        events = requests.get("http://open-api.myhelsinki.fi/v1/places/", params={"distance_filter":distance_filter,"start":currentPos})

        for entry in events.json()["data"]:
            if (entry["opening_hours"]["hours"] == None):
                continue
            for day in entry["opening_hours"]["hours"]:
                if (day["opens"] == None or day["closes"] == None):
                    continue

                for targetDay in dayList:
                    if (targetDay.weekday() == day["weekday_id"]):
                        entryStart = pd.to_datetime(targetDay.isoformat()) + datetime.timedelta(hours=int(day["opens"][0:2]), minutes=int(day["opens"][3:5]))
                        entryEnd = pd.to_datetime(targetDay.isoformat()) + datetime.timedelta(hours=int(day["closes"][0:2]), minutes=int(day["closes"][3:5]))

                        entryStart = startDate if startDate > entryStart else entryStart
                        entryEnd = endDate if entryEnd > endDate else entryEnd

                        startPos = getMinutes(entryStart - startDate) // 2
                        endPos = getMinutes(entryEnd - startDate) // 2
                        lastAddedOne = 0

                        for i in range(startPos, endPos):
                            result[i] += 1

        lastAddition = int(events.json()["meta"]["count"])
        currentPos += lastAddition
        print(currentPos, lastAddedOne)

    return result


total = {}
for row in stations.index:
    total[stations["serial"][row] + "events"] = DoEvent(row)
    total[stations["serial"][row] + "places"] = DoPlace(row)

pd.DataFrame(data=total).to_csv("eventsPlaces.csv")
