import requests
import xml.etree.ElementTree as ET
from sklearn import linear_model
from celery import Celery

app = Celery('tasks')
app.config_from_object('celeryconfig')

@app.task
def getWeatherData(location):
    places = {'london': {"lat": "51.50", "lon": "0.12"},
              'madrid': {"lat": "40.41", "lon": "3.70"},
              'newyork': {"lat": "40.71", "lon": "74.00"},
              'shanghai': {"lat": "31.23", "lon": "116.47"},}
    result = ''
    if location in places.keys():
        uri = f'http://www.7timer.info/bin/api.pl?lon={places[location]["lon"]}&lat={places[location]["lat"]}&product=civil&output=xml'
        r = requests.get(uri)
        if r.status_code == 200:
            result = r.text
        else:
            print("LOCATION NOT RECOGNISED")
    return result

@app.task
def parseData(xml_doc):
    root = ET.fromstring(xml_doc)
    dataseries = root.find('dataseries')
    wind_x = []
    wind_y = []
    for data in dataseries.findall('data'):
        wind_speed = data.find('wind10m_speed')
        time = int(data.attrib['timepoint'][:-1])
        speed = float(wind_speed.text)
        wind_x.append([time])
        wind_y.append(speed)
    return [wind_x, wind_y]

@app.task
def fitData(data):
    reg = linear_model.LinearRegression()
    reg.fit(data[0], data[1])
    return [float(reg.coef_), float(reg.intercept_)]