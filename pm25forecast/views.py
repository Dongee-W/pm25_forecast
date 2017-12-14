from django.http import HttpResponse
from django.shortcuts import render

import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def overview_test(request):
    context = {'filename': "overview_2017112707.csv"}
    return render(request, 'overview.html', context)

def overview(request):
    import pytz
    import datetime
    current=datetime.datetime.now(pytz.timezone('Asia/Taipei'))
    name=current.strftime('%Y%m%d%H')

    dateString = str(current.year) + '{0:02d}'.format(current.month) + '{0:02d}'.format(current.day)
    hourString = '{0:02d}'.format(current.hour)
    
    # parameters for testing
    
    dateString = '20171127'
    hourString = '16'
    
    # parameters end ...

    import mysql.connector
    cnx = mysql.connector.connect(user='root', password='360iisnrl', host='127.0.0.1', database='pm25_forecast')
    cursor = cnx.cursor()
    queryLeft = "select ID, HOUR_AHEAD, PREDICTION from predictions where TARGET_DATE = %s and TARGET_HOUR = %s"
    cursor.execute(queryLeft, (dateString, hourString))

    leftHalfData = []
    for (id, hour_ahead, prediction) in cursor:
        record = {"ID": id, "HOUR_AHEAD": hour_ahead, "PREDICTION": float(prediction)}
        leftHalfData.append(record)

    queryRight = "select ID, HOUR_AHEAD, PREDICTION from predictions where DATE = %s and HOUR = %s"
    cursor.execute(queryRight, (dateString, hourString))

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


    if len(leftHalfData) > 0 and len(rightHalfData) > 0 and len(dataNow) > 0:
        import pandas as pd
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

        perfectTable.to_csv(os.path.join(BASE_DIR, "static/overview_" + dateString + hourString + ".csv"), index=False)
    else:
        return HttpResponse("Data not available right now, try again later.")
    
    context = {'filename': ("overview_" + dateString + hourString + ".csv")}

    return render(request, 'overview.html', context)

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
    
    dateString = '20171127'
    hourString = '16'
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

    cursor.close()
    cnx.close()

    if len(data) > 0:
        import pandas as pd
        queryResult = pd.DataFrame(data)
        queryResult['TIMESTAMP'] = queryResult['DATE'] + queryResult['HOUR']
        final = queryResult.drop(["DATE", "HOUR"], axis=1)
        final.to_csv(os.path.join(BASE_DIR, "static/" + station_id + ".csv"), index=False)
    
        context = {'station_id': station_id, 'filename': (station_id + ".csv")}
        return render(request, 'forecast-page.html', context)
    else:
        return HttpResponse("Data not available right now, try again later.")

def performance_test(request):
    return render(request, 'performance.html')


def performance(request):
    '''
    import mysql.connector
    cnx = mysql.connector.connect(user='root', password='360iisnrl', host='127.0.0.1', database='pm25_forecast')
    cursor = cnx.cursor()
    query = "select p.HOUR_AHEAD, p.PREDICTION, r.READING from predictions p, readings r where p.ID = r.ID and p.TARGET_DATE = r.DATE and p.TARGET_HOUR = r.HOUR and MODEL = 0"
    cursor.execute(query)

    data = []
    for (hour_ahead, prediction, real) in cursor:
        record = {"HOUR_AHEAD": float(hour_ahead), "PREDICTION": float(prediction), "REAL": float(real)}
        data.append(record)

    import pandas as pd
    table = pd.DataFrame(data)
    table['RELATIVE_ERROR'] = abs(table['REAL'] - table['PREDICTION'])/table['REAL']
    '''

    return render(request, 'performance.html')
