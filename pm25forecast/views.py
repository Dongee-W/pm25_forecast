from django.http import HttpResponse
from django.shortcuts import render
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def forecast(request, station_id):
    
    import mysql.connector
    cnx = mysql.connector.connect(user='root',password='360chenghua', host='127.0.0.1',database='pm25_readings')
    cursor = cnx.cursor()
    timestrings = "('20171030', '07'),('20171030', '08'),('20171030', '09'),('20171030', '10'),('20171030', '11'),('20171030', '12e')"
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
    
    context = {'station_id': station_id, 'filename': (station_id + ".csv")}
    return render(request, 'forecast-page.html', context)

def experiment(request):
    return HttpResponse("This is meant to be an experiment.")
