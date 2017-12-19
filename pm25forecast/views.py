from django.http import HttpResponse
from django.shortcuts import render

import os
import datetime
import pytz

import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def overview_test(request):
    context = {'filename': "overview_2017112707.csv"}
    return render(request, 'overview.html', context)

def overview(request, model_id):

    current=datetime.datetime.now(pytz.timezone('Asia/Taipei'))
    name=current.strftime('%Y-%m-%d %I%p')

    dateString = str(current.year) + '{0:02d}'.format(current.month) + '{0:02d}'.format(current.day)
    hourString = '{0:02d}'.format(current.hour)

    # parameters for testing
    '''
    dateString = '20171127'
    hourString = '16'
    '''

    # parameters end ...

    import mysql.connector
    cnx = mysql.connector.connect(user='root', password='360iisnrl', host='127.0.0.1', database='pm25_forecast')
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
        record = {"ID": id, "READING": reading}
        dataNow.append(record)


    if (str(model_id) == '0'):
        modelName = "Mahajan"
    else:
        modelName = "Yang"

    if len(leftHalfData) > 0 and len(rightHalfData) > 0 and len(dataNow) > 0:
        resultSetLeft = pd.DataFrame(leftHalfData)
        resultSetRight = pd.DataFrame(rightHalfData)
        resultSetNow = pd.DataFrame(dataNow).set_index('ID')
        leftHalfTable = resultSetLeft.pivot_table(values='PREDICTION',index=['ID'], columns=['HOUR_AHEAD'])
        leftHalfTable.columns = [str(col) + "left" for col in leftHalfTable.columns]
        rightHalfTable = resultSetRight.pivot_table(values='PREDICTION',index=['ID'], columns=['HOUR_AHEAD'])
        rightHalfTable.columns = [str(col) + "right" for col in rightHalfTable.columns]

        fullTable = pd.merge(leftHalfTable, rightHalfTable, how='outer', left_index=True, right_index=True)
        perfectTable = pd.merge(fullTable, resultSetNow, how='left', left_index=True, right_index=True)
        perfectTable['ID'] = perfectTable.index

        perfectTable.to_csv(os.path.join(BASE_DIR, "static/overview_" + dateString + hourString + "_" + model_id + ".csv"), index=False)
    else:
        
        adjusted = current - datetime.timedelta(hours = 1)
        adjustName=adjusted.strftime('%Y-%m-%d %I%p')

        adjustDateString = str(adjusted.year) + '{0:02d}'.format(adjusted.month) + '{0:02d}'.format(adjusted.day)
        adjustHourString = '{0:02d}'.format(adjusted.hour)
        context = {'filename': ("overview_" + adjustDateString + adjustHourString + "_" + model_id + ".csv"), 'modelName': modelName, 'lastUpdate': adjustName}

        return render(request, 'overview.html', context)
    

    context = {'filename': ("overview_" + dateString + hourString + "_" + model_id + ".csv"), 'modelName': modelName, 'lastUpdate': name}

    cursor.close()
    cnx.close()

    return render(request, 'overview.html', context)

def forecast_test(request):
    context = {'station_id': "WF_3977799", 'filename': "1421GE.csv"}
    return render(request, 'forecast-page.html', context)

def forecast(request, station_id):
    import pytz
    import datetime
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
    cnx = mysql.connector.connect(user='root', password='360iisnrl', host='127.0.0.1', database='pm25_forecast')
    cursor = cnx.cursor()
    query = "select ID, DATE, HOUR, READING from readings where ID = %s and DATE = %s and HOUR = %s"
    cursor.execute(query, (station_id, dateString, hourString))

    data = []
    for (id, date, hour, reading) in cursor:
        record = {"ID": id, "DATE": date, "HOUR": hour, "READING": reading}
        data.append(record)

    query_predicion = "select ID, DATE, HOUR, HOUR_AHEAD, PREDICTION from predictions where ID = %s and DATE = %s and HOUR = %s and MODEL = 0 ORDER BY HOUR_AHEAD"
    cursor.execute(query_predicion, (station_id, dateString, hourString))
    for (id, date, hour, hour_ahead, prediction) in cursor:
        targetTime = datetime.datetime.strptime(date + hour, '%Y%m%d%H') + datetime.timedelta(hours = hour_ahead)
        targetDate = str(targetTime.year) + '{0:02d}'.format(targetTime.month) + '{0:02d}'.format(targetTime.day)
        targetHour = '{0:02d}'.format(targetTime.hour)
        record = {"ID": id, "DATE": targetDate, "HOUR": targetHour, "READING": prediction}
        data.append(record)

    

    if len(data) > 1:
        queryResult = pd.DataFrame(data)
        queryResult['TIMESTAMP'] = queryResult['DATE'] + queryResult['HOUR']
        final = queryResult.drop(["DATE", "HOUR"], axis=1)
        final.to_csv(os.path.join(BASE_DIR, "static/" + station_id + ".csv"), index=False)
    
        context = {'station_id': station_id, 'filename': (station_id + ".csv"), 'lastUpdate': name}
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

        context = {'station_id': station_id, 'filename': (station_id + ".csv"), 'lastUpdate': adjustName}
        return render(request, 'forecast-page.html', context)

    cursor.close()
    cnx.close()

        

def main_test(request):
    context = {'xaxis': "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]", 'dataStringM_1': "[10, 9.2, 9.0, 7.9, 7.5, 4,  3, 2, 1, 0]", 'dataStringY_1': "[10, 9.6, 9.3, 8.9, 7.5, 4,  3, 2, 1, 0]"}
    return render(request, 'main.html', context)


def main(request):

    import mysql.connector
    cnx = mysql.connector.connect(user='root', password='360iisnrl', host='127.0.0.1', database='pm25_forecast')
    cursor = cnx.cursor()
    query = "select p.MODEL, p.HOUR_AHEAD, p.PREDICTION, r.READING from predictions p, readings r where p.ID = r.ID and p.TARGET_DATE = r.DATE and p.TARGET_HOUR = r.HOUR"
    cursor.execute(query)

    data = []
    for (model_id, hour_ahead, prediction, real) in cursor:
        record = {"MODEL": int(model_id), "HOUR_AHEAD": float(hour_ahead), "PREDICTION": float(prediction), "REAL": float(real)}
        data.append(record)

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

    dataStringM_1 = str(cdfM_1.tolist())
    dataStringY_1 = str(cdfY_1.tolist())
    dataStringM_2 = str(cdfM_2.tolist())
    dataStringY_2 = str(cdfY_2.tolist())
    dataStringM_3 = str(cdfM_3.tolist())
    dataStringY_3 = str(cdfY_3.tolist())
    dataStringM_4 = str(cdfM_4.tolist())
    dataStringY_4 = str(cdfY_4.tolist())
    dataStringM_5 = str(cdfM_5.tolist())
    dataStringY_5 = str(cdfY_5.tolist())

    xaxis = str(histoM_1[1].tolist())

    medianError = full.groupby(['MODEL','HOUR_AHEAD'])['RELATIVE_ERROR'].median()

    context = {'xaxis': xaxis, 'dataStringM_1': dataStringM_1, 'dataStringY_1': dataStringY_1, 
    'dataStringM_2': dataStringM_2, 'dataStringY_2': dataStringY_2,
    'dataStringM_3': dataStringM_3, 'dataStringY_3': dataStringY_3,
    'dataStringM_4': dataStringM_4, 'dataStringY_4': dataStringY_4,
    'dataStringM_5': dataStringM_5, 'dataStringY_5': dataStringY_5,
    'medianErrorM_1': int(round(medianError[0][1]*100)), 'medianErrorM_2': int(round(medianError[0][2]*100)),
    'medianErrorM_3': int(round(medianError[0][3]*100)), 'medianErrorM_4': int(round(medianError[0][4]*100)),
    'medianErrorM_5': int(round(medianError[0][5]*100)), 'medianErrorY_1': int(round(medianError[1][1]*100)),
    'medianErrorY_2': int(round(medianError[1][2]*100)), 'medianErrorY_3': int(round(medianError[1][3]*100)),
    'medianErrorY_4': int(round(medianError[1][4]*100)), 'medianErrorY_5': int(round(medianError[1][5]*100))
    }
    
    cursor.close()
    cnx.close()

    return render(request, 'main.html', context)
