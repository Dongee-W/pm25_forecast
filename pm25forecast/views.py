from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def forecast(request, station_id):
    context = {'station_id': station_id}
    return render(request, 'forecast-page.html', context)

def experiment(request):
    return HttpResponse("This is meant to be an experiment.")
