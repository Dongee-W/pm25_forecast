from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def forecast(request):
    return HttpResponse("Welcome to forecast page.")

def experiment(request):
    return HttpResponse("This is meant to be an experiment.")
