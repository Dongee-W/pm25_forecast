from django.http import HttpResponse
from django.shortcuts import render

import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def forecast_test(request):
    context = {'station_id': "WF_3977799", 'filename': "1421GE.csv"}
    return render(request, 'forecast-page.html', context)


def forecast(request, station_id):
    
    import pytz
    import datetime
    current=datetime.datetime.now(pytz.timezone('Asia/Taipei'))
    name=current.strftime('%Y%m%d%H')


    dateString = str(current.year) + '{0:02d}'.format(current.month) + '{0:02d}'.format(current.day)
    hourString = '{0:02d}'.format(current.hour)

    # parameters for testing
    '''
    dateString = '20171031'
    hourString = '10'
    station_id = 'FT_LIVE8CE7A9EC_G5N'
    '''
    # parameters end ...

    import mysql.connector
    cnx = mysql.connector.connect(user='root', password='360chenghua', host='127.0.0.1', database='pm25_readings')
    cursor = cnx.cursor()
    query = "select ID, DATE, HOUR, READING from readings where ID = %s and DATE = %s and HOUR = %s"
    cursor.execute(query, (station_id, dateString, hourString))

    data = []
    for (id, date, hour, reading) in cursor:
        record = {"ID": id, "DATE": date, "HOUR": hour, "READING": reading}
        data.append(record)

    query_predicion = "select ID, DATE, HOUR, TARGET_HOUR, PREDICTION from predictions where ID = %s and DATE = %s and HOUR = %s and MODEL = 0 ORDER BY TARGET_HOUR"
    cursor.execute(query_predicion, (station_id, dateString, hourString))
    for (id, date, hour, target_hour, prediction) in cursor:
        targetTime = datetime.datetime.strptime(date + hour, '%Y%m%d%H') + datetime.timedelta(hours = target_hour)
        targetDate = str(targetTime.year) + '{0:02d}'.format(targetTime.month) + '{0:02d}'.format(targetTime.day)
        targetHour = '{0:02d}'.format(targetTime.hour)

        record = {"ID": id, "DATE": targetDate, "HOUR": targetHour, "READING": prediction}
        data.append(record)


    cursor.close()
    cnx.close()

    import pandas as pd
    queryResult = pd.DataFrame(data)
    queryResult['TIMESTAMP'] = queryResult['DATE'] + queryResult['HOUR']
    final = queryResult.drop(["DATE", "HOUR"], axis=1)
    final.to_csv(os.path.join(BASE_DIR, "static/" + station_id + ".csv"), index=False)
    
    context = {'station_id': station_id, 'filename': (station_id + ".csv")}
    return render(request, 'forecast-page.html', context)

def experiment(request):
    '''
    import pytz
    import datetime
    current=datetime.datetime.now(pytz.timezone('Asia/Taipei'))
    name=current.strftime('%Y%m%d%H')
    n = range(1, 7)
    tsList = [current - datetime.timedelta(hours = d) for d in n]
    queryTime = [(str(ts.year) + '{0:02d}'.format(ts.month) + '{0:02d}'.format(ts.day), '{0:02d}'.format(ts.hour)) for ts in tsList]
    timestrings = str(queryTime).replace("[", "").replace("]", "")

    import mysql.connector
    cnx = mysql.connector.connect(user='root',password='360chenghua', host='127.0.0.1',database='pm25_readings')
    cursor = cnx.cursor()
    query = "select ID, DATE, HOUR, READING from readings where ID = %s and (DATE, HOUR) IN (" + timestrings + ")"
    cursor.execute(query,(station_id,))

    data = []
    for (id, date, hour, reading) in cursor:
        record = {"ID": id, "DATE": date, "HOUR": hour, "READING": reading}
        data.append(record)

    cursor.close()
    cnx.close()

    import pandas as pd
    queryResult = pd.DataFrame(data)
    queryResult['TIMESTAMP'] = queryResult['DATE'] + queryResult['HOUR']
    final = queryResult.drop(["DATE", "HOUR"], axis=1)
    final.to_csv(os.path.join(BASE_DIR, "static/" + station_id + ".csv"), index=False)
    '''
    return HttpResponse("This is meant to be an experiment.")
