"""pm25forecast URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.main, name='main'),
    url(r'^overview-test/$', views.overview_test, name='overview_test'),
    url(r'^idw-test/$', views.idw_test, name='idw_test'),
    url(r'^idw/(?P<model_id>[0-9]+)$', views.idw, name='idw'),
    url(r'^overview/(?P<model_id>[0-9]+)$', views.overview, name='overview'),
    url(r'^forecast-test/$', views.forecast_test, name='forecast_test'),
    url(r'^forecast/(?P<station_id>[a-zA-Z0-9\.\-\_]+)', views.forecast, name='forecast'),
    url(r'^main-test/', views.main_test, name='main_test'),
    #url(r'^/', views.main, name='main'),
]
