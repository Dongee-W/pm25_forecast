from django.http import HttpResponse
from django.shortcuts import render

import os
import datetime
import pytz
from pathlib import Path
import json

import pandas as pd
import numpy as np

from . import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def index(request):
    return render(request, 'index.html')

def overview_test(request):
    context = {'csvFile': "overview_2018011719_cluster.csv", 'modelName': "Mahajan", 'lastUpdate': "2018-01-18 09AM", 'modelId': 1, "isClustered": "true"}
    return render(request, 'overview.html', context)

def overview(request, model_id):

    current=datetime.datetime.now(pytz.timezone('Asia/Taipei'))
    name=current.strftime('%Y-%m-%d %I%p')

    dateString = str(current.year) + '{0:02d}'.format(current.month) + '{0:02d}'.format(current.day)
    hourString = '{0:02d}'.format(current.hour)

    if (str(model_id) == '0'):
        modelName = "Mahajan"
    else:
        modelName = "Yang"

    lastest_file = Path(os.path.join(BASE_DIR, "static/overview_" + dateString + hourString + "_" + model_id + ".csv"))

    # This is for performance, but this will not get updated once the file is created.
    #if lastest_file.is_file():
    #    context = {'filename': ("overview_" + dateString + hourString + "_" + model_id + ".csv"), 'modelName': modelName, 'lastUpdate': name}
    #    return render(request, 'overview.html', context)

    # parameters for testing
    '''
    dateString = '20171127'
    hourString = '16'
    '''

    # Temporary Use
    if(model_id == "3"): 
        withClustering = True
        model_id = 0
    else:
        withClustering = False

    # parameters end ...

    import mysql.connector
    cnx = mysql.connector.connect(user=config.mysql["user"], password=config.mysql["password"], host='127.0.0.1', database=config.mysql["database"])
    cursor = cnx.cursor()
    queryLeft = "select ID, HOUR_AHEAD, PREDICTION from predictions where TARGET_DATE = %s and TARGET_HOUR = %s and MODEL = %s"
    cursor.execute(queryLeft, (dateString, hourString, str(model_id)))

    leftHalfData = []
    for (id, hour_ahead, prediction) in cursor:
        record = {"ID": id, "HOUR_AHEAD": hour_ahead, "PREDICTION": float(prediction)}
        leftHalfData.append(record)

    queryRight = "select ID, HOUR_AHEAD, PREDICTION from predictions where DATE = %s and HOUR = %s and MODEL = %s"
    cursor.execute(queryRight, (dateString, hourString, str(model_id)))

    rightHalfData= []
    for (id, hour_ahead, prediction) in cursor:
        record = {"ID": id, "HOUR_AHEAD": hour_ahead, "PREDICTION": float(prediction)}
        rightHalfData.append(record)

    queryNow = "select ID, READING from readings where DATE = %s and HOUR = %s"
    cursor.execute(queryNow, (dateString, hourString))

    dataNow = []
    for (id, reading) in cursor:
        record = {"ID": id, "READING": float(reading)}
        dataNow.append(record)

    if len(leftHalfData) > 0 and len(rightHalfData) > 0 and len(dataNow) > 0:
        resultSetLeft = pd.DataFrame(leftHalfData)
        resultSetRight = pd.DataFrame(rightHalfData)
        resultSetNow = pd.DataFrame(dataNow).set_index('ID')
        leftHalfTable = resultSetLeft.pivot_table(values='PREDICTION',index=['ID'], columns=['HOUR_AHEAD'])
        leftHalfTable.columns = ["now-" + str(col) + "h" for col in leftHalfTable.columns]
        rightHalfTable = resultSetRight.pivot_table(values='PREDICTION',index=['ID'], columns=['HOUR_AHEAD'])
        rightHalfTable.columns = ["now+" + str(col) + "h" for col in rightHalfTable.columns]
        fullTable = pd.merge(leftHalfTable, rightHalfTable, how='outer', left_index=True, right_index=True)
        resultSetNow.columns = ['now']
        perfectTable = pd.merge(fullTable, resultSetNow, how='left', left_index=True, right_index=True)
        perfectTable['device_id'] = perfectTable.index
        allColumns = ["device_id", "now-5h", "now-4h", "now-3h", "now-2h", "now-1h", "now", "now+1h", "now+2h", "now+3h", "now+4h", "now+5h"]
        for col in allColumns:
            if col not in perfectTable:
                perfectTable[col] = np.nan
        perfectTable = perfectTable[["device_id", "now-5h", "now-4h", "now-3h", "now-2h", "now-1h", "now", "now+1h", "now+2h", "now+3h", "now+4h", "now+5h"]]
        cluster = pd.read_csv("/home/pm25_forecast/complete.csv")

        ultimate = pd.merge(perfectTable, cluster, how="inner", left_on="device_id", right_on="ID").drop("ID", axis = 1)
        ultimate.to_csv(os.path.join(BASE_DIR, "static/overview_" + dateString + hourString + "_" + model_id + ".csv"), index=False)

        sourceString = "pm25-forecast-yang by IIS-NRL"
        versionString = current.strftime('%Y-%m-%dT%H:%M:%SZ')
        numRecords = len(perfectTable)
        dateStringJson = current.strftime('%Y-%m-%d')
        timeString = hourString + ":00"
        feeds = ultimate.to_dict(orient="records")
        jsonString = json.dumps({"source": sourceString, "version": versionString, "num_of_records": numRecords, "date": dateString, "time": timeString, "feed": feeds})

        with open(os.path.join(BASE_DIR, "static/overview_" + dateString + hourString + "_" + model_id + ".json"), "w") as jsonFile:
            jsonFile.write(jsonString)

        context = {'csvFile': ("overview_" + dateString + hourString + "_" + model_id + ".csv"), 'jsonFile': ("overview_" + dateString + hourString + "_" + model_id + ".json"), 'modelName': modelName, 'lastUpdate': name, 'modelId': model_id, 'isClustered': withClustering}
        cursor.close()
        cnx.close()
        return render(request, 'overview.html', context)
    else:
        
        adjusted = current - datetime.timedelta(hours = 1)
        adjustName=adjusted.strftime('%Y-%m-%d %I%p')

        adjustDateString = str(adjusted.year) + '{0:02d}'.format(adjusted.month) + '{0:02d}'.format(adjusted.day)
        adjustHourString = '{0:02d}'.format(adjusted.hour)


        context = {'csvFile': ("overview_" + adjustDateString + adjustHourString + "_" + model_id + ".csv"), 'jsonFile': ("overview_" + adjustDateString + adjustHourString + "_" + model_id + ".json"), 'modelName': modelName, 'lastUpdate': adjustName, 'modelId': model_id, 'isClustered': withClustering}

        return render(request, 'overview.html', context)
    

'''
forecast_test is for the demonstration purpose.
'''
def forecast_test(request):
    context = {'station_id': "WF_3977799", 'filename': "1421GE.csv", 'lastUpdate': "2018-01-18 09AM", 'lat': "23.97571", 'lon': "120.704944"}
    return render(request, 'forecast-page.html', context)

def forecast(request, station_id):
    current=datetime.datetime.now(pytz.timezone('Asia/Taipei'))
    name=current.strftime('%Y-%m-%d %I%p')

    dateString = str(current.year) + '{0:02d}'.format(current.month) + '{0:02d}'.format(current.day)
    hourString = '{0:02d}'.format(current.hour)
    
    # parameters for testing
    '''
    dateString = '20171127'
    hourString = '16'
    '''
    #station_id = 'FT_LIVE8CE7A9EC_G5N'
    
    # parameters end ...

    import mysql.connector
    cnx = mysql.connector.connect(user=config.mysql["user"], password=config.mysql["password"], host='127.0.0.1', database=config.mysql["database"])
    cursor = cnx.cursor()

    query = "select ID, LATITUDE, LONGTITUDE from gps where ID = %s"
    cursor.execute(query, (station_id, ))
    gps = []

    for (id, lat, lon) in cursor:
        recordGPS = {"ID": id, "LATITUDE": lat, "LONGTITUDE": lon}
        gps.append(recordGPS)

    try:
        latitude = str(float(gps[0]['LATITUDE']))
        longtitude = str(float(gps[0]['LONGTITUDE']))
    except:
        latitude = "Latitude not available"
        longtitude = "Longtitude not available"
        

    query = "select ID, DATE, HOUR, READING from readings where ID = %s and DATE = %s and HOUR = %s"
    cursor.execute(query, (station_id, dateString, hourString))

    data = []
    for (id, date, hour, reading) in cursor:
        record = {"ID": id, "DATE": date, "HOUR": hour, "READING": reading}
        data.append(record)

    query_predicion = "select ID, DATE, HOUR, HOUR_AHEAD, PREDICTION from predictions where ID = %s and DATE = %s and HOUR = %s ORDER BY MODEL, HOUR_AHEAD"
    cursor.execute(query_predicion, (station_id, dateString, hourString))

    counter = 0
    for (id, date, hour, hour_ahead, prediction) in cursor:
        targetTime = datetime.datetime.strptime(date + hour, '%Y%m%d%H') + datetime.timedelta(hours = hour_ahead)
        targetDate = str(targetTime.year) + '{0:02d}'.format(targetTime.month) + '{0:02d}'.format(targetTime.day)
        targetHour = '{0:02d}'.format(targetTime.hour)
        record = {"ID": id, "DATE": targetDate, "HOUR": targetHour, "READING": prediction}
        if counter < 5:
            data.append(record) 
            counter += 1

    
    if len(data) > 1:
        queryResult = pd.DataFrame(data)
        queryResult['TIMESTAMP'] = queryResult['DATE'] + queryResult['HOUR']
        final = queryResult.drop(["DATE", "HOUR"], axis=1)
        final.to_csv(os.path.join(BASE_DIR, "static/" + station_id + ".csv"), index=False)
    
        context = {'station_id': station_id, 'filename': (station_id + ".csv"), 'lastUpdate': name, 'lat': latitude, 'lon': longtitude}
        return render(request, 'forecast-page.html', context)
    else:
        adjusted = current - datetime.timedelta(hours = 1)
        adjustName=adjusted.strftime('%Y-%m-%d %I%p')

        adjustDateString = str(adjusted.year) + '{0:02d}'.format(adjusted.month) + '{0:02d}'.format(adjusted.day)
        adjustHourString = '{0:02d}'.format(adjusted.hour)

        query = "select ID, DATE, HOUR, READING from readings where ID = %s and DATE = %s and HOUR = %s"
        cursor.execute(query, (station_id, adjustDateString, adjustHourString))

        data = []
        for (id, date, hour, reading) in cursor:
            record = {"ID": id, "DATE": date, "HOUR": hour, "READING": reading}
            data.append(record)

        query_predicion = "select ID, DATE, HOUR, HOUR_AHEAD, PREDICTION from predictions where ID = %s and DATE = %s and HOUR = %s and MODEL = 0 ORDER BY HOUR_AHEAD"
        cursor.execute(query_predicion, (station_id, adjustDateString, adjustHourString))
        for (id, date, hour, hour_ahead, prediction) in cursor:
            targetTime = datetime.datetime.strptime(date + hour, '%Y%m%d%H') + datetime.timedelta(hours = hour_ahead)
            targetDate = str(targetTime.year) + '{0:02d}'.format(targetTime.month) + '{0:02d}'.format(targetTime.day)
            targetHour = '{0:02d}'.format(targetTime.hour)
            record = {"ID": id, "DATE": targetDate, "HOUR": targetHour, "READING": prediction}
            data.append(record)
        queryResult = pd.DataFrame(data)
        queryResult['TIMESTAMP'] = queryResult['DATE'] + queryResult['HOUR']
        final = queryResult.drop(["DATE", "HOUR"], axis=1)
        final.to_csv(os.path.join(BASE_DIR, "static/" + station_id + ".csv"), index=False)

        context = {'station_id': station_id, 'filename': (station_id + ".csv"), 'lastUpdate': adjustName, 'lat': latitude, 'lon': longtitude}
        return render(request, 'forecast-page.html', context)

    cursor.close()
    cnx.close()

'''
main_test is for the demonstration purpose.
'''
def main_test(request):
    with open(os.path.join(BASE_DIR, "static/main_2018011720.txt")) as f:
        content = f.readlines()
        content = [x.strip() for x in content]

        xaxis = content[0]
        dataStringM_1 = content[1]
        dataStringY_1 = content[2]
        dataStringM_2 = content[3]
        dataStringY_2 = content[4]
        dataStringM_3 = content[5] 
        dataStringY_3 = content[6] 
        dataStringM_4 = content[7] 
        dataStringY_4 = content[8] 
        dataStringM_5 = content[9] 
        dataStringY_5 = content[10]
        statistics_0_1 = content[11]
        statistics_0_2 = content[12]
        statistics_0_3 = content[13]
        statistics_0_4 = content[14]
        statistics_0_5 = content[15]
        statistics_1_1 = content[16]
        statistics_1_2 = content[17]
        statistics_1_3 = content[18]
        statistics_1_4 = content[19]
        statistics_1_5 =content[20]

    context = {'xaxis': xaxis, 'dataStringM_1': dataStringM_1, 'dataStringY_1': dataStringY_1, 
    'dataStringM_2': dataStringM_2, 'dataStringY_2': dataStringY_2,
    'dataStringM_3': dataStringM_3, 'dataStringY_3': dataStringY_3,
    'dataStringM_4': dataStringM_4, 'dataStringY_4': dataStringY_4,
    'dataStringM_5': dataStringM_5, 'dataStringY_5': dataStringY_5,
    'medianErrorM_1': statistics_0_1, 'medianErrorM_2': statistics_0_2,
    'medianErrorM_3': statistics_0_3, 'medianErrorM_4': statistics_0_4,
    'medianErrorM_5': statistics_0_5, 'medianErrorY_1': statistics_1_1,
    'medianErrorY_2': statistics_1_2, 'medianErrorY_3': statistics_1_3,
    'medianErrorY_4': statistics_1_4, 'medianErrorY_5': statistics_1_5
    }
    return render(request, 'main.html', context)

'''
main is the function for main page.
'''
def abmain(request):

    current=datetime.datetime.now(pytz.timezone('Asia/Taipei'))

    dateString = str(current.year) + '{0:02d}'.format(current.month) + '{0:02d}'.format(current.day)
    hourString = '{0:02d}'.format(current.hour)
    filename = os.path.join(BASE_DIR, "static/main_" + dateString + hourString + ".txt")

    lastest_file = Path(filename)

    if lastest_file.is_file():
        with open(filename) as f:
            content = f.readlines()
        content = [x.strip() for x in content]


        xaxis = content[0]
        dataStringM_1 = content[1]
        dataStringY_1 = content[2]
        dataStringM_2 = content[3]
        dataStringY_2 = content[4]
        dataStringM_3 = content[5] 
        dataStringY_3 = content[6] 
        dataStringM_4 = content[7] 
        dataStringY_4 = content[8] 
        dataStringM_5 = content[9] 
        dataStringY_5 = content[10]
        statistics_0_1 = content[11]
        statistics_0_2 = content[12]
        statistics_0_3 = content[13]
        statistics_0_4 = content[14]
        statistics_0_5 = content[15]
        statistics_1_1 = content[16]
        statistics_1_2 = content[17]
        statistics_1_3 = content[18]
        statistics_1_4 = content[19]
        statistics_1_5 =content[20]
    else:
        import mysql.connector
        cnx = mysql.connector.connect(user=config.mysql["user"], password=config.mysql["password"], host='127.0.0.1', database=config.mysql["database"])
        cursor = cnx.cursor()
        query = "select p.MODEL, p.HOUR_AHEAD, p.PREDICTION, r.READING from predictions p, readings r where p.ID = r.ID and p.TARGET_DATE = r.DATE and p.TARGET_HOUR = r.HOUR and r.DATE > %s"

        outOfDate = current + datetime.timedelta(days=-5)
        outOfDateString = (str(outOfDate.year) + '{0:02d}'.format(outOfDate.month) + '{0:02d}'.format(outOfDate.day),)

        cursor.execute(query, outOfDateString)

        data = []
        for (model_id, hour_ahead, prediction, real) in cursor:
            record = {"MODEL": int(model_id), "HOUR_AHEAD": float(hour_ahead), "PREDICTION": float(prediction), "REAL": float(real)}
            data.append(record)
        
        cursor.close()
        cnx.close()

        table = pd.DataFrame(data)
        table['RELATIVE_ERROR'] = abs(table['REAL'] - table['PREDICTION'])/table['REAL']
        full = table.replace([np.inf, -np.inf], np.nan).dropna()

        seriesM_1 = full[(full['MODEL'] == 0) & (full['HOUR_AHEAD'] == 1)]['RELATIVE_ERROR']
        seriesY_1 = full[(full['MODEL'] == 1) & (full['HOUR_AHEAD'] == 1)]['RELATIVE_ERROR']
        seriesM_2 = full[(full['MODEL'] == 0) & (full['HOUR_AHEAD'] == 2)]['RELATIVE_ERROR']
        seriesY_2 = full[(full['MODEL'] == 1) & (full['HOUR_AHEAD'] == 2)]['RELATIVE_ERROR']
        seriesM_3 = full[(full['MODEL'] == 0) & (full['HOUR_AHEAD'] == 3)]['RELATIVE_ERROR']
        seriesY_3 = full[(full['MODEL'] == 1) & (full['HOUR_AHEAD'] == 3)]['RELATIVE_ERROR']
        seriesM_4 = full[(full['MODEL'] == 0) & (full['HOUR_AHEAD'] == 4)]['RELATIVE_ERROR']
        seriesY_4 = full[(full['MODEL'] == 1) & (full['HOUR_AHEAD'] == 4)]['RELATIVE_ERROR']
        seriesM_5 = full[(full['MODEL'] == 0) & (full['HOUR_AHEAD'] == 5)]['RELATIVE_ERROR']
        seriesY_5 = full[(full['MODEL'] == 1) & (full['HOUR_AHEAD'] == 5)]['RELATIVE_ERROR']

        histoM_1 = np.histogram(seriesM_1.values, range=(0, 1), bins=20, normed=True)
        histoY_1 = np.histogram(seriesY_1.values, range=(0, 1), bins=20, normed=True)
        histoM_2 = np.histogram(seriesM_2.values, range=(0, 1), bins=20, normed=True)
        histoY_2 = np.histogram(seriesY_2.values, range=(0, 1), bins=20, normed=True)
        histoM_3 = np.histogram(seriesM_3.values, range=(0, 1), bins=20, normed=True)
        histoY_3 = np.histogram(seriesY_3.values, range=(0, 1), bins=20, normed=True)
        histoM_4 = np.histogram(seriesM_4.values, range=(0, 1), bins=20, normed=True)
        histoY_4 = np.histogram(seriesY_4.values, range=(0, 1), bins=20, normed=True)
        histoM_5 = np.histogram(seriesM_5.values, range=(0, 1), bins=20, normed=True)
        histoY_5 = np.histogram(seriesY_5.values, range=(0, 1), bins=20, normed=True)

        cdfM_1 = np.cumsum(histoM_1[0])
        cdfY_1 = np.cumsum(histoY_1[0])
        cdfM_2 = np.cumsum(histoM_2[0])
        cdfY_2 = np.cumsum(histoY_2[0])
        cdfM_3 = np.cumsum(histoM_3[0])
        cdfY_3 = np.cumsum(histoY_3[0])
        cdfM_4 = np.cumsum(histoM_4[0])
        cdfY_4 = np.cumsum(histoY_4[0])
        cdfM_5 = np.cumsum(histoM_5[0])
        cdfY_5 = np.cumsum(histoY_5[0])

        dataStringM_1 = str([p / 20 for p in cdfM_1.tolist()])
        dataStringY_1 = str([p / 20 for p in cdfY_1.tolist()])
        dataStringM_2 = str([p / 20 for p in cdfM_2.tolist()])
        dataStringY_2 = str([p / 20 for p in cdfY_2.tolist()])
        dataStringM_3 = str([p / 20 for p in cdfM_3.tolist()])
        dataStringY_3 = str([p / 20 for p in cdfY_3.tolist()])
        dataStringM_4 = str([p / 20 for p in cdfM_4.tolist()])
        dataStringY_4 = str([p / 20 for p in cdfY_4.tolist()])
        dataStringM_5 = str([p / 20 for p in cdfM_5.tolist()])
        dataStringY_5 = str([p / 20 for p in cdfY_5.tolist()])

        xaxis = str(histoM_1[1].tolist())

        medianError = full.groupby(['MODEL','HOUR_AHEAD'])['RELATIVE_ERROR'].median()
        statistics_0_1 = str(int(round(medianError[0][1]*100)))
        statistics_0_2 = str(int(round(medianError[0][2]*100)))
        statistics_0_3 = str(int(round(medianError[0][3]*100)))
        statistics_0_4 = str(int(round(medianError[0][4]*100)))
        statistics_0_5 = str(int(round(medianError[0][5]*100)))
        statistics_1_1 = str(int(round(medianError[1][1]*100)))
        statistics_1_2 = str(int(round(medianError[1][2]*100)))
        statistics_1_3 = str(int(round(medianError[1][3]*100)))
        statistics_1_4 = str(int(round(medianError[1][4]*100)))
        statistics_1_5 = str(int(round(medianError[1][5]*100)))

        with open(filename, "w") as text_file:
            text_file.write(xaxis + "\n")
            text_file.write(dataStringM_1 + "\n")
            text_file.write(dataStringY_1 + "\n")
            text_file.write(dataStringM_2 + "\n")
            text_file.write(dataStringY_2 + "\n")
            text_file.write(dataStringM_3 + "\n")
            text_file.write(dataStringY_3 + "\n")
            text_file.write(dataStringM_4 + "\n")
            text_file.write(dataStringY_4 + "\n")
            text_file.write(dataStringM_5 + "\n")
            text_file.write(dataStringY_5 + "\n")
            text_file.write(statistics_0_1 + "\n")
            text_file.write(statistics_0_2 + "\n")
            text_file.write(statistics_0_3 + "\n")
            text_file.write(statistics_0_4 + "\n")
            text_file.write(statistics_0_5 + "\n")
            text_file.write(statistics_1_1 + "\n")
            text_file.write(statistics_1_2 + "\n")
            text_file.write(statistics_1_3 + "\n")
            text_file.write(statistics_1_4 + "\n")
            text_file.write(statistics_1_5 + "\n")

    context = {'xaxis': xaxis, 'dataStringM_1': dataStringM_1, 'dataStringY_1': dataStringY_1, 
    'dataStringM_2': dataStringM_2, 'dataStringY_2': dataStringY_2,
    'dataStringM_3': dataStringM_3, 'dataStringY_3': dataStringY_3,
    'dataStringM_4': dataStringM_4, 'dataStringY_4': dataStringY_4,
    'dataStringM_5': dataStringM_5, 'dataStringY_5': dataStringY_5,
    'medianErrorM_1': statistics_0_1, 'medianErrorM_2': statistics_0_2,
    'medianErrorM_3': statistics_0_3, 'medianErrorM_4': statistics_0_4,
    'medianErrorM_5': statistics_0_5, 'medianErrorY_1': statistics_1_1,
    'medianErrorY_2': statistics_1_2, 'medianErrorY_3': statistics_1_3,
    'medianErrorY_4': statistics_1_4, 'medianErrorY_5': statistics_1_5
    }

    return render(request, 'main.html', context)

def idw_test(request):
    return render(request, 'idw.html')

def idw(request, model_id):
    '''
    11 hours data including 6 hours of real value and 5 hours of prediction.
    This piece of data is for the animation on the website.
    '''

    current=datetime.datetime.now(pytz.timezone('Asia/Taipei'))
    name=current.strftime('%Y%m%d%H')

    dateString = str(current.year) + '{0:02d}'.format(current.month) + '{0:02d}'.format(current.day)
    hourString = '{0:02d}'.format(current.hour)

    # Produce timestamp
    n = range(0, 6)
    tsList = [current - datetime.timedelta(hours = d) for d in n]
    dateList = np.array([str(ts.year) + '{0:02d}'.format(ts.month) + '{0:02d}'.format(ts.day) for ts in tsList])
    hourList = np.array(['{0:02d}'.format(ts.hour) for ts in tsList])

    dhList = list(zip(dateList, hourList))
    conList = list(map(lambda x: "(DATE=\'" + str(x[0]) + "\' AND HOUR=\'" + str(x[1]) + "\')", dhList))
    whereclause = " OR ".join(conList)

    import mysql.connector
    cnx = mysql.connector.connect(user=config.mysql["user"], password=config.mysql["password"], host='127.0.0.1', database=config.mysql["database"])
    cursor = cnx.cursor()
    queryPastNow = "select ID, DATE, HOUR, READING from readings where " + whereclause
    cursor.execute(queryPastNow)

    leftHalfData= []
    for (id, date, hour, reading) in cursor:
        record = {"ID": id, "DATE": date, "HOUR": hour, "READING": float(reading)}
        leftHalfData.append(record)

    queryRight = "select ID, HOUR_AHEAD, PREDICTION from predictions where DATE = %s and HOUR = %s and MODEL = %s"
    cursor.execute(queryRight, (dateString, hourString, str(model_id)))

    rightHalfData= []
    for (id, hour_ahead, prediction) in cursor:
        record = {"ID": id, "HOUR_AHEAD": hour_ahead, "PREDICTION": float(prediction)}
        rightHalfData.append(record)

    if len(leftHalfData) > 0 and len(rightHalfData) > 0:
        resultSetLeft = pd.DataFrame(leftHalfData)
        resultSetRight = pd.DataFrame(rightHalfData)
        resultSetLeft["TS"] = resultSetLeft["DATE"] + resultSetLeft["HOUR"]
        leftHalfTable = resultSetLeft.drop(["DATE", "HOUR"], axis=1).pivot_table(values='READING',index=['ID'], columns=['TS'])
        rightHalfTable = resultSetRight.pivot_table(values='PREDICTION',index=['ID'], columns=['HOUR_AHEAD'])

        rightHalfTable.columns = [str(col) + "right" for col in rightHalfTable.columns]

        fullTable = pd.merge(leftHalfTable, rightHalfTable, how='inner', left_index=True, right_index=True)

        query = "select ID, LATITUDE, LONGTITUDE from gps"
        cursor.execute(query)
        gps = []

        for (id, lat, lon) in cursor:
            try:
                recordGPS = {"ID": id, "LATITUDE": float(lat), "LONGTITUDE": float(lon)}
            except:
                recordGPS = {"ID": id, "LATITUDE": np.nan, "LONGTITUDE": np.nan}
            gps.append(recordGPS)
        resultSetGPS = pd.DataFrame(gps).set_index('ID').dropna()

        perfectTable = pd.merge(fullTable, resultSetGPS, how='inner', left_index=True, right_index=True)

        outputReady = [list(zip(perfectTable[perfectTable.columns[-2]], 
            perfectTable[perfectTable.columns[-1]],
            perfectTable[perfectTable.columns[i]])) for  i in range(0, 11)]

        outputString = "var PM25points = " + json.dumps(outputReady)

        # Timestamp for ouput
        tsOutput = [(current + datetime.timedelta(hours = d)).strftime('%Y-%m-%d %I%p') for d in range(-5,6)]
        tsOutputString = "var timestamps = " + json.dumps(tsOutput)

        filename = os.path.join(BASE_DIR, "static/animation_" + dateString + hourString + "_" + str(model_id) + ".js")

        with open(filename, "w") as text_file:
            text_file.write(outputString + "\n")
            text_file.write(tsOutputString + "\n")

        context = {'filename': "animation_" + dateString + hourString + "_" + str(model_id) + ".js"}
    else:
        adjusted = current - datetime.timedelta(hours = 1)
        adjustName=adjusted.strftime('%Y-%m-%d %I%p')

        adjustDateString = str(adjusted.year) + '{0:02d}'.format(adjusted.month) + '{0:02d}'.format(adjusted.day)
        adjustHourString = '{0:02d}'.format(adjusted.hour)
        context = {'filename': ("animation_" + adjustDateString + adjustHourString + "_" + str(model_id) + ".js")}

    cursor.close()
    cnx.close()
    return render(request, 'idw.html', context)

'''
main is the function for main page.
'''
def epamain(request):

    current=datetime.datetime.now(pytz.timezone('Asia/Taipei'))
    name=current.strftime('%Y-%m-%d %I%p')

    dateString = str(current.year) + '{0:02d}'.format(current.month) + '{0:02d}'.format(current.day)
    hourString = '{0:02d}'.format(current.hour)
    import mysql.connector
    cnx = mysql.connector.connect(user=config.mysql["user"], password=config.mysql["password"], host='127.0.0.1', database=config.mysql["database"])
    cursor = cnx.cursor()

    performanceCache = os.path.join(BASE_DIR, "static/epa/main_" + dateString + hourString + ".json")

    pc = Path(performanceCache)

    if pc.is_file():
        with open(performanceCache) as f:
            data = json.load(f)
            statistics_0_1 = data[0]
            statistics_0_2 = data[1]
            statistics_0_3 = data[2]
            statistics_0_4 = data[3]
            statistics_0_5 = data[4]
    else:
        query = "select p.MODEL, p.HOUR_AHEAD, p.PREDICTION, r.READING from predictions p, readingsEPA r where p.ID = r.ID and p.TARGET_DATE = r.DATE and p.TARGET_HOUR = r.HOUR and r.DATE > %s"

        outOfDate = current + datetime.timedelta(days=-2)
        outOfDateString = (str(outOfDate.year) + '{0:02d}'.format(outOfDate.month) + '{0:02d}'.format(outOfDate.day),)

        cursor.execute(query, outOfDateString)
        
        data = []
        for (model_id, hour_ahead, prediction, real) in cursor:
            record = {"MODEL": int(model_id), "HOUR_AHEAD": float(hour_ahead), "PREDICTION": float(prediction), "REAL": float(real)}
            data.append(record)
        
        

        table = pd.DataFrame(data)
        table['RELATIVE_ERROR'] = abs(table['REAL'] - table['PREDICTION'])/table['REAL']
        full = table.replace([np.inf, -np.inf], np.nan).dropna()

        medianError = full.groupby(['MODEL','HOUR_AHEAD'])['RELATIVE_ERROR'].median()
        statistics_0_1 = str(int(round(medianError[6][1]*100)))
        statistics_0_2 = str(int(round(medianError[6][2]*100)))
        statistics_0_3 = str(int(round(medianError[6][3]*100)))
        statistics_0_4 = str(int(round(medianError[6][4]*100)))
        statistics_0_5 = str(int(round(medianError[6][5]*100)))

    model_id = "6"
    modelName = "Mahajan"

    queryLeft = "select ID, HOUR_AHEAD, PREDICTION from predictions where TARGET_DATE = %s and TARGET_HOUR = %s and MODEL = %s"
    cursor.execute(queryLeft, (dateString, hourString, str(model_id)))

    leftHalfData = []
    for (id, hour_ahead, prediction) in cursor:
        record = {"ID": id, "HOUR_AHEAD": hour_ahead, "PREDICTION": float(prediction)}
        leftHalfData.append(record)

    queryRight = "select ID, HOUR_AHEAD, PREDICTION from predictions where DATE = %s and HOUR = %s and MODEL = %s"
    cursor.execute(queryRight, (dateString, hourString, str(model_id)))

    rightHalfData= []
    for (id, hour_ahead, prediction) in cursor:
        record = {"ID": id, "HOUR_AHEAD": hour_ahead, "PREDICTION": float(prediction)}
        rightHalfData.append(record)

    queryNow = "select ID, READING from readingsEPA where DATE = %s and HOUR = %s"
    cursor.execute(queryNow, (dateString, hourString))

    dataNow = []
    for (id, reading) in cursor:
        record = {"ID": id, "READING": float(reading)}
        dataNow.append(record)

    if len(leftHalfData) > 0 and len(rightHalfData) > 0 and len(dataNow) > 0:

        resultSetLeft = pd.DataFrame(leftHalfData)
        resultSetRight = pd.DataFrame(rightHalfData)
        resultSetNow = pd.DataFrame(dataNow).set_index('ID')
        leftHalfTable = resultSetLeft.pivot_table(values='PREDICTION',index=['ID'], columns=['HOUR_AHEAD'])
        leftHalfTable.columns = ["now-" + str(col) + "h" for col in leftHalfTable.columns]
        rightHalfTable = resultSetRight.pivot_table(values='PREDICTION',index=['ID'], columns=['HOUR_AHEAD'])
        rightHalfTable.columns = ["now+" + str(col) + "h" for col in rightHalfTable.columns]

        fullTable = pd.merge(leftHalfTable, rightHalfTable, how='outer', left_index=True, right_index=True)
        resultSetNow.columns = ['now']
        perfectTable = pd.merge(fullTable, resultSetNow, how='left', left_index=True, right_index=True)
        perfectTable['device_id'] = perfectTable.index

        allColumns = ["device_id", "now-5h", "now-4h", "now-3h", "now-2h", "now-1h", "now", "now+1h", "now+2h", "now+3h", "now+4h", "now+5h"]
        for col in allColumns:
            if col not in perfectTable:
                perfectTable[col] = np.nan

        perfectTable = perfectTable[["device_id", "now-5h", "now-4h", "now-3h", "now-2h", "now-1h", "now", "now+1h", "now+2h", "now+3h", "now+4h", "now+5h"]]

        perfectTable.to_csv(os.path.join(BASE_DIR, "static/epa/overview_" + dateString + hourString + "_" + model_id + ".csv"), index=False)

        sourceString = "pm25-forecast-yang by IIS-NRL"
        versionString = current.strftime('%Y-%m-%dT%H:%M:%SZ')
        numRecords = len(perfectTable)
        dateStringJson = current.strftime('%Y-%m-%d')
        timeString = hourString + ":00"
        feeds = perfectTable.to_dict(orient="records")
        jsonString = json.dumps({"source": sourceString, "version": versionString, "num_of_records": numRecords, "date": dateString, "time": timeString, "feed": feeds})

        with open(os.path.join(BASE_DIR, "static/epa/overview_" + dateString + hourString + "_" + model_id + ".json"), "w") as jsonFile:
            jsonFile.write(jsonString)

        
        context = {'csvFile': ("epa/overview_" + dateString + hourString + "_" + model_id + ".csv"), 'jsonFile': ("epa/overview_" + dateString + hourString + "_" + model_id + ".json"), 'modelName': modelName, 'lastUpdate': name, 'modelId': model_id, 'medianErrorM_1': statistics_0_1, 'medianErrorM_2': statistics_0_2,
            'medianErrorM_3': statistics_0_3, 'medianErrorM_4': statistics_0_4,
            'medianErrorM_5': statistics_0_5}
        
    else:
        adjusted = current - datetime.timedelta(hours = 1)
        adjustName=adjusted.strftime('%Y-%m-%d %I%p')

        adjustDateString = str(adjusted.year) + '{0:02d}'.format(adjusted.month) + '{0:02d}'.format(adjusted.day)
        adjustHourString = '{0:02d}'.format(adjusted.hour)
        context = {'csvFile': ("epa/overview_" + adjustDateString + adjustHourString + "_" + model_id + ".csv"), 'jsonFile': ("epa/overview_" + adjustDateString + adjustHourString + "_" + model_id + ".json"), 'modelName': modelName, 'lastUpdate': adjustName, 'modelId': model_id, 'medianErrorM_1': statistics_0_1, 'medianErrorM_2': statistics_0_2,
            'medianErrorM_3': statistics_0_3, 'medianErrorM_4': statistics_0_4,
            'medianErrorM_5': statistics_0_5}

    cursor.close()
    cnx.close()

    return render(request, 'epa-main.html', context)